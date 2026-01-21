"""
Flask API应用
提供多个页面和查询接口
"""
import os
import sys
import time
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import logging
from datetime import datetime
from collections import defaultdict
from threading import Lock


# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入配置文件
try:
    from config.db import config
except ImportError as e:
    print(f"❌ 导入配置文件失败: {e}")
    print("请确保 config/db.py 文件存在")
    sys.exit(1)

# 导入数据库模块
try:
    from DB.database import db_manager
except ImportError as e:
    print(f"❌ 导入数据库模块失败: {e}")
    print("请确保 DB/database.py 文件存在")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建Flask应用
# 设置模板文件夹为当前目录下的templates文件夹
app = Flask(__name__, template_folder='templates')
CORS(app)  # 允许跨域

@app.after_request
def after_request(response):
    """添加跨域响应头 - 确保前端能正常调用API"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Max-Age', '86400')  # 24小时
    return response

# 应用配置
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['JSON_AS_ASCII'] = False  # 支持中文
app.config['JSON_SORT_KEYS'] = False  # 保持原始顺序

# ============================================
# 🟢 新增：请求频率限制配置
# ============================================
class RateLimiter:
    """简单的请求频率限制器"""

    def __init__(self):
        # 存储每个IP的请求时间戳
        self.request_history = defaultdict(list)
        # 线程锁，确保线程安全
        self.lock = Lock()
        # 清理过期记录的时间间隔（秒）
        self.cleanup_interval = 60
        self.last_cleanup = time.time()

    def is_allowed(self, ip_address, limit=2, window=1):
        """
        检查是否允许请求

        参数:
            ip_address: 客户端IP地址
            limit: 时间窗口内允许的最大请求数（默认为2）
            window: 时间窗口大小（秒，默认为1秒）

        返回:
            allowed: 是否允许请求
            remaining_time: 需要等待的时间（秒）
        """
        current_time = time.time()

        # 定期清理过期记录
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_expired(window)
            self.last_cleanup = current_time

        with self.lock:
            # 获取该IP的请求历史
            timestamps = self.request_history[ip_address]

            # 移除超出时间窗口的记录
            valid_timestamps = [ts for ts in timestamps if current_time - ts < window]
            self.request_history[ip_address] = valid_timestamps

            # 检查是否超过限制
            if len(valid_timestamps) >= limit:
                # 计算需要等待的时间
                oldest_timestamp = min(valid_timestamps)
                remaining_time = window - (current_time - oldest_timestamp)
                return False, max(0, remaining_time)

            # 添加当前请求时间戳
            self.request_history[ip_address].append(current_time)
            return True, 0

    def _cleanup_expired(self, window):
        """清理过期的请求记录"""
        current_time = time.time()
        with self.lock:
            expired_ips = []
            for ip, timestamps in self.request_history.items():
                # 保留在时间窗口内的记录
                valid_timestamps = [ts for ts in timestamps if current_time - ts < window * 2]
                if valid_timestamps:
                    self.request_history[ip] = valid_timestamps
                else:
                    expired_ips.append(ip)

            # 删除没有有效记录的IP
            for ip in expired_ips:
                del self.request_history[ip]

    def get_stats(self, ip_address=None):
        """获取限制器统计信息"""
        current_time = time.time()
        with self.lock:
            if ip_address:
                if ip_address in self.request_history:
                    timestamps = self.request_history[ip_address]
                    recent = [ts for ts in timestamps if current_time - ts < 10]
                    return {
                        'ip': ip_address,
                        'total_requests': len(timestamps),
                        'recent_requests': len(recent),
                        'last_request': max(timestamps) if timestamps else None
                    }
                else:
                    return {'ip': ip_address, 'message': 'No requests recorded'}
            else:
                return {
                    'total_ips': len(self.request_history),
                    'total_requests': sum(len(timestamps) for timestamps in self.request_history.values())
                }

# 创建全局频率限制器实例
rate_limiter = RateLimiter()

def get_client_ip():
    """获取客户端真实IP地址"""
    if request.headers.get('X-Forwarded-For'):
        # 处理代理情况
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    else:
        ip = request.remote_addr
    return ip

def apply_rate_limit(limit=2, window=1):
    """应用频率限制装饰器"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            client_ip = get_client_ip()
            allowed, wait_time = rate_limiter.is_allowed(client_ip, limit, window)

            if not allowed:
                logger.warning(f"🚫 请求频率限制 - IP: {client_ip}, 路径: {request.path}, 需等待: {wait_time:.2f}秒")
                return jsonify({
                    'success': False,
                    'error': f'请求过于频繁，请等待 {wait_time:.1f} 秒后重试',
                    'code': 'RATE_LIMIT_EXCEEDED',
                    'wait_time': wait_time,
                    'ip': client_ip,
                    'limit': limit,
                    'window': window,
                    'timestamp': datetime.now().isoformat()
                }), 429  # 429 Too Many Requests

            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator
# ============================================
# 🟢 新增内容结束
# ============================================

# 添加应用启动时的初始化标志
_app_initialized = False

def initialize_app():
    """初始化应用"""
    global _app_initialized
    if not _app_initialized:
        logger.info(f"应用初始化，当前环境: {config.ENV}")
        logger.info(f"数据库配置: {config.db_config.host}:{config.db_config.port}/{config.db_config.database}")

        # 测试数据库连接
        try:
            db_healthy = db_manager.health_check()
            if db_healthy:
                logger.info("✅ 数据库连接成功")
            else:
                logger.warning("⚠️ 数据库连接失败，请检查配置")
        except Exception as e:
            logger.error(f"数据库连接测试失败: {str(e)}")

        _app_initialized = True

# 使用 before_request 替代 before_first_request
@app.before_request
def before_request_handler():
    """在每个请求前执行，确保应用已初始化"""
    initialize_app()

    # ============================================
    # 🟢 新增：全局请求日志和统计
    # ============================================
    # 排除静态文件和健康检查
    excluded_paths = ['/static/', '/health', '/favicon.ico']
    if not any(request.path.startswith(path) for path in excluded_paths):
        client_ip = get_client_ip()
        logger.info(f"🌐 请求: {request.method} {request.path} - IP: {client_ip}")

# ========== 通用页面渲染函数 ==========
def render_template_page(page_name):
    """通用页面渲染函数"""
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    page_path = os.path.join(template_dir, f'{page_name}.html')

    logger.debug(f"尝试访问页面: {page_name}.html")
    logger.debug(f"文件路径: {page_path}")

    if os.path.exists(page_path):
        logger.debug(f"✅ 找到 {page_name}.html 文件")
        try:
            return render_template(f'{page_name}.html')
        except Exception as e:
            logger.error(f"渲染 {page_name} 模板失败: {e}")
            try:
                with open(page_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return content
            except Exception as e2:
                logger.error(f"读取 {page_name} 文件失败: {e2}")
                return f"<h1>访问 {page_name} 页面失败: {e2}</h1>", 500
    else:
        logger.warning(f"⚠️ {page_name}.html 文件不存在: {page_path}")
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>页面未找到 - {page_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 40px; text-align: center; }}
                h1 {{ color: #e74c3c; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>⚠️ 页面未找到</h1>
                <p>页面 <strong>{page_name}.html</strong> 不存在</p>
                <p>请确保该文件位于 templates 文件夹中</p>
                <p><a href="/">返回首页</a></p>
            </div>
        </body>
        </html>
        """, 404

# ========== 页面路由（不带后缀）==========
@app.route('/', methods=['GET'])
def index():
    """首页"""
    return render_template_page('index')

@app.route('/encode', methods=['GET'])
def encode_page():
    """雷神加解密页面"""
    return render_template_page('encode')

@app.route('/ocpc', methods=['GET'])
def ocpc_page():
    """OCPC查询页面"""
    return render_template_page('ocpc')

@app.route('/api-test', methods=['GET'])
def api_test_page():
    """API测试页面"""
    return render_template_page('api-test')

@app.route('/documentation', methods=['GET'])
def documentation_page():
    """使用文档页面"""
    return render_template_page('documentation')

@app.route('/about', methods=['GET'])
def about_page():
    """关于我们页面"""
    return render_template_page('about')

# ========== 页面路由（带.html后缀）==========
@app.route('/index.html', methods=['GET'])
def index_html():
    """首页（带.html后缀）"""
    return render_template_page('index')

@app.route('/encode.html', methods=['GET'])
def encode_html():
    """雷神加解密页面（带.html后缀）"""
    return render_template_page('encode')

@app.route('/ocpc.html', methods=['GET'])
def ocpc_html():
    """OCPC查询页面（带.html后缀）"""
    return render_template_page('ocpc')

@app.route('/api-test.html', methods=['GET'])
def api_test_html():
    """API测试页面（带.html后缀）"""
    return render_template_page('api-test')

@app.route('/documentation.html', methods=['GET'])
def documentation_html():
    """使用文档页面（带.html后缀）"""
    return render_template_page('documentation')

@app.route('/about.html', methods=['GET'])
def about_html():
    """关于我们页面（带.html后缀）"""
    return render_template_page('about')

# ========== 静态文件服务 ==========
@app.route('/static/<path:filename>')
def static_files(filename):
    """提供静态文件"""
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    if os.path.exists(static_dir):
        return send_from_directory('static', filename)
    else:
        logger.warning(f"静态文件夹不存在: {static_dir}")
        return jsonify({'error': 'Static file not found'}), 404

# ========== API接口 ==========
@app.route('/api', methods=['GET'])
@apply_rate_limit(limit=5, window=10)  # 🟢 新增：API信息页面频率限制
def api_info():
    """API首页 - 返回JSON信息"""
    db_healthy = db_manager.health_check()
    return jsonify({
        'service': 'OCPC Query API',
        'version': '1.0.0',
        'status': 'running',
        'environment': config.ENV,
        'database': {
            'status': 'connected' if db_healthy else 'disconnected',
            'host': config.db_config.host,
            'port': config.db_config.port,
            'database': config.db_config.database
        },
        'endpoints': {
            'health_check': '/health',
            'query_ocpc_mapping': f'{config.API_PREFIX}/query/ocpc-mapping?channel=bytes&order=desc',
            'query_ocpc_log': f'{config.API_PREFIX}/query/ocpc-log?channel=360&order=desc',
            'batch_query': f'{config.API_PREFIX}/query/batch (POST)',
            'rate_limit_stats': '/api/rate-limit-stats'  # 🟢 新增：频率限制统计接口
        },
        'timestamp': datetime.now().isoformat()
    })

# 🟢 新增：频率限制统计接口
@app.route('/api/rate-limit-stats', methods=['GET'])
def rate_limit_stats():
    """获取频率限制统计信息"""
    ip = request.args.get('ip')
    stats = rate_limiter.get_stats(ip)
    return jsonify({
        'success': True,
        'stats': stats,
        'timestamp': datetime.now().isoformat()
    })

# 健康检查端点
@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    try:
        # 检查数据库连接
        db_healthy = db_manager.health_check()

        status_code = 200 if db_healthy else 503
        status_text = 'healthy' if db_healthy else 'unhealthy'

        return jsonify({
            'status': status_text,
            'timestamp': datetime.now().isoformat(),
            'environment': config.ENV,
            'database': {
                'connected': db_healthy,
                'host': config.db_config.host,
                'port': config.db_config.port,
                'database': config.db_config.database
            }
        }), status_code
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503

# ========== OCPC查询API ==========
@app.route(f'{config.API_PREFIX}/query/ocpc-mapping', methods=['GET'])
@apply_rate_limit(limit=2, window=1)  # 🟢 新增：1秒内最多2次请求
def query_ocpc_mapping():
    """
    查询 ocpc_mapping 表数据
    """
    try:
        # 获取查询参数
        channel = request.args.get('channel', 'bytes')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        order = request.args.get('order', 'desc')
        env = request.args.get('env', config.ENV)
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', config.DEFAULT_PAGE_SIZE, type=int)

        # 验证参数
        if not channel:
            return jsonify({
                'success': False,
                'error': 'channel参数不能为空',
                'code': 'PARAM_ERROR'
            }), 400

        # 构建SQL查询和参数
        sql_parts = ["SELECT * FROM `tbl_ocpc_mapping` WHERE `channel` = %s"]
        params = [channel]

        if start_time:
            sql_parts.append("AND `create_time` >= %s")
            params.append(start_time)

        if end_time:
            sql_parts.append("AND `create_time` <= %s")
            params.append(end_time)

        sql_parts.append(f"ORDER BY `create_time` {order.upper()}")
        sql = " ".join(sql_parts)
        params_tuple = tuple(params)

        # 执行分页查询
        result = db_manager.query_paginate(
            sql=sql,
            params=params_tuple,
            page=page,
            page_size=page_size,
            env=env
        )

        return jsonify({
            'success': True,
            'data': result['items'],
            'pagination': {
                'page': result['page'],
                'page_size': result['page_size'],
                'total': result['total'],
                'total_pages': result['total_pages']
            },
            'query_info': {
                'channel': channel,
                'start_time': start_time,
                'end_time': end_time,
                'order': order,
                'environment': env,
                'database': config.db_config.database,
                'sql': sql,
                'params': list(params_tuple)
            },
            'rate_limit_info': {  # 🟢 新增：返回频率限制信息
                'applied': True,
                'limit': 2,
                'window': 1
            },
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"查询ocpc_mapping失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '服务器内部错误',
            'code': 'INTERNAL_ERROR',
            'detail': str(e) if config.DEBUG else None
        }), 500

@app.route(f'{config.API_PREFIX}/query/ocpc-log', methods=['GET'])
@apply_rate_limit(limit=2, window=1)  # 🟢 新增：1秒内最多2次请求
def query_ocpc_log():
    """
    查询 ocpc_log 表数据
    """
    try:
        # 获取查询参数
        channel = request.args.get('channel', '360')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        order = request.args.get('order', 'desc')
        env = request.args.get('env', config.ENV)
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', config.DEFAULT_PAGE_SIZE, type=int)

        if not channel:
            return jsonify({
                'success': False,
                'error': 'channel参数不能为空',
                'code': 'PARAM_ERROR'
            }), 400

        # 构建SQL
        sql_parts = ["SELECT * FROM `tbl_ocpc_log` WHERE `channel` = %s"]
        params = [channel]

        if start_time:
            sql_parts.append("AND `create_time` >= %s")
            params.append(start_time)

        if end_time:
            sql_parts.append("AND `create_time` <= %s")
            params.append(end_time)

        sql_parts.append(f"ORDER BY `create_time` {order.upper()}")
        sql = " ".join(sql_parts)
        params_tuple = tuple(params)

        # 执行查询
        result = db_manager.query_paginate(
            sql=sql,
            params=params_tuple,
            page=page,
            page_size=page_size,
            env=env
        )

        return jsonify({
            'success': True,
            'data': result['items'],
            'pagination': {
                'page': result['page'],
                'page_size': result['page_size'],
                'total': result['total'],
                'total_pages': result['total_pages']
            },
            'query_info': {
                'channel': channel,
                'start_time': start_time,
                'end_time': end_time,
                'order': order,
                'environment': env,
                'database': config.db_config.database,
                'sql': sql,
                'params': list(params_tuple)
            },
            'rate_limit_info': {  # 🟢 新增：返回频率限制信息
                'applied': True,
                'limit': 2,
                'window': 1
            },
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"查询ocpc_log失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '服务器内部错误',
            'code': 'INTERNAL_ERROR',
            'detail': str(e) if config.DEBUG else None
        }), 500

@app.route(f'{config.API_PREFIX}/query/batch', methods=['POST'])
@apply_rate_limit(limit=1, window=2)  # 🟢 新增：2秒内最多1次批量请求
def batch_query():
    """
    批量查询接口
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空',
                'code': 'PARAM_ERROR'
            }), 400

        queries = data.get('queries', [])
        env = data.get('env', config.ENV)

        if not isinstance(queries, list) or len(queries) == 0:
            return jsonify({
                'success': False,
                'error': 'queries参数必须是非空数组',
                'code': 'PARAM_ERROR'
            }), 400

        results = []
        for i, query in enumerate(queries):
            try:
                table = query.get('table')
                channel = query.get('channel')
                start_time = query.get('start_time')
                end_time = query.get('end_time')
                order = query.get('order', 'desc')

                if not table or not channel:
                    results.append({
                        'success': False,
                        'error': f'第{i+1}个查询缺少table或channel参数',
                        'index': i
                    })
                    continue

                if table not in ['ocpc_mapping', 'ocpc_log']:
                    results.append({
                        'success': False,
                        'error': f'第{i+1}个查询table参数必须是ocpc_mapping或ocpc_log',
                        'index': i
                    })
                    continue

                # 构建SQL
                table_name = f"tbl_ocpc_{'mapping' if table == 'ocpc_mapping' else 'log'}"
                sql_parts = [f"SELECT * FROM `{table_name}` WHERE `channel` = %s"]
                params = [channel]

                if start_time:
                    sql_parts.append("AND `create_time` >= %s")
                    params.append(start_time)

                if end_time:
                    sql_parts.append("AND `create_time` <= %s")
                    params.append(end_time)

                sql_parts.append(f"ORDER BY `create_time` {order.upper()}")
                sql = " ".join(sql_parts)

                # 执行查询
                data_result = db_manager.execute_query(sql, tuple(params), env)

                results.append({
                    'success': True,
                    'table': table,
                    'channel': channel,
                    'start_time': start_time,
                    'end_time': end_time,
                    'order': order,
                    'count': len(data_result),
                    'data': data_result,
                    'index': i
                })

            except Exception as e:
                results.append({
                    'success': False,
                    'error': f'第{i+1}个查询执行失败: {str(e)}',
                    'index': i
                })

        return jsonify({
            'success': True,
            'results': results,
            'environment': env,
            'rate_limit_info': {  # 🟢 新增：返回频率限制信息
                'applied': True,
                'limit': 1,
                'window': 2
            },
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"批量查询失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '服务器内部错误',
            'code': 'INTERNAL_ERROR'
        }), 500

# ========== 错误处理 ==========
@app.errorhandler(404)
def page_not_found(e):
    """处理404错误"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>页面未找到 - 404</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 40px; text-align: center; }}
            h1 {{ color: #e74c3c; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>⚠️ 404 - 页面未找到</h1>
            <p>您访问的页面不存在</p>
            <p><a href="/">返回首页</a></p>
        </div>
    </body>
    </html>
    """, 404

@app.errorhandler(429)
def rate_limit_exceeded(e):
    """处理429 Too Many Requests错误"""
    return jsonify({
        'success': False,
        'error': '请求过于频繁，请稍后再试',
        'code': 'RATE_LIMIT_EXCEEDED',
        'timestamp': datetime.now().isoformat(),
        'message': '为了保护服务器资源，您的请求频率已超过限制'
    }), 429

if __name__ == '__main__':
    # 应用启动时立即初始化（用于命令行启动时显示信息）
    print("=" * 80)
    print("🚀 工具箱前端服务启动")
    print("=" * 80)
    print(f"📋 环境: {config.ENV}")
    print(f"🗄️ 数据库: {config.db_config.host}:{config.db_config.port}/{config.db_config.database}")
    print(f"🔗 API前缀: {config.API_PREFIX}")
    print("=" * 80)

    # 检查模板文件夹
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(base_dir, 'templates')

    if os.path.exists(template_dir):
        print(f"✅ 模板文件夹: {template_dir}")
        files = os.listdir(template_dir)
        html_files = [f.replace('.html', '') for f in files if f.endswith('.html')]
        print(f"📄 可用页面 ({len(html_files)}个): {html_files}")
    else:
        print(f"❌ 模板文件夹不存在")

    print("=" * 80)
    print("🌐 页面路由:")
    print("  🏠 首页: http://localhost:5000/ 或 http://localhost:5000/index.html")
    # print("  🔒 雷神加解密: http://localhost:5000/encode 或 http://localhost:5000/encode.html")
    # print("  📊 OCPC查询: http://localhost:5000/ocpc 或 http://localhost:5000/ocpc.html")
    # print("  🔌 API测试: http://localhost:5000/api-test 或 http://localhost:5000/api-test.html")
    # print("  📖 使用文档: http://localhost:5000/documentation 或 http://localhost:5000/documentation.html")
    # print("  ℹ️ 关于我们: http://localhost:5000/about 或 http://localhost:5000/about.html")
    # print("=" * 80)
    # print("⚡ API接口:")
    # print(f"  📊 API信息: http://localhost:5000/api")
    # print(f"  ❤️ 健康检查: http://localhost:5000/health")
    # print(f"  📈 OCPC查询: http://localhost:5000{config.API_PREFIX}/query/ocpc-mapping?channel=bytes&order=desc")
    # print(f"  📝 OCPC日志: http://localhost:5000{config.API_PREFIX}/query/ocpc-log?channel=360&order=desc")
    print(f"  📊 频率限制统计: http://localhost:5000/api/rate-limit-stats")
    print("=" * 80)
    print("⚠️ 频率限制配置:")
    print("  🔄 OCPC查询接口: 1秒内最多2次请求")
    print("  🔄 批量查询接口: 2秒内最多1次请求")
    print("  📊 API信息接口: 10秒内最多5次请求")
    print("=" * 80)

    # 手动初始化应用
    initialize_app()

    # 启动Flask应用
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=config.DEBUG,
        threaded=True
    )