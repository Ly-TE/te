"""
Flask API应用
提供多个页面和查询接口
"""
import logging
import os
import sys
import time
import json
from collections import defaultdict
from datetime import datetime
from threading import Lock

from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS

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

# 配置日志(提前配置，在导入工具模块前)
logging.basicConfig(level=logging.DEBUG if config.DEBUG else logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入工具模块
try:
    from utils import SDKLogDecryptor, CryptoUtils, IdCardCryptoHandler
    logger.info("✅ 工具模块导入成功")
except ImportError as e:
    logger.warning(f"⚠️ 工具模块导入失败: {e}")
    logger.warning("部分功能可能不可用")
    SDKLogDecryptor = None
    CryptoUtils = None
    IdCardCryptoHandler = None

# 导入服务模块
try:
    from services import OCPCService
    ocpc_service = OCPCService(db_manager)
    logger.info("✅ OCPC服务初始化成功")
except ImportError as e:
    logger.warning(f"⚠️ 服务模块导入失败: {e}")
    logger.warning("OCPC查询功能可能不可用")
    OCPCService = None
    ocpc_service = None

try:
    from services.user_channel_service import UserChannelService
    user_channel_service = UserChannelService(db_manager)
    logger.info("✅ 用户渠道服务初始化成功")
except ImportError as e:
    logger.warning(f"⚠️ 用户渠道服务模块导入失败: {e}")
    logger.warning("用户渠道修改功能可能不可用")
    UserChannelService = None
    user_channel_service = None

# 导入统一登录服务
try:
    from services.token_service import token_service
    logger.info("✅ 统一登录服务初始化成功")
except ImportError as e:
    logger.warning(f"⚠️ 统一登录服务模块导入失败: {e}")
    token_service = None

# 获取当前文件所在的目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 在应用创建前定义蓝图注册函数
def register_blueprints():
    """注册所有蓝图"""
    try:
        from api.auth_api import auth_bp
        app.register_blueprint(auth_bp)
        logger.info("✅ 统一登录API蓝图注册成功")
    except ImportError as e:
        logger.warning(f"⚠️ 统一登录API蓝图注册失败: {e}")
    except Exception as e:
        logger.error(f"蓝图注册异常: {e}")

# ========== 第1处修改：使用绝对路径配置Flask ==========
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'),  # 绝对路径
            static_folder=os.path.join(BASE_DIR, 'static')  # 绝对路径
            )
CORS(app)  # 允许跨域

# 立即注册所有蓝图
register_blueprints()


@app.after_request
def after_request(response):
    """添加跨域响应头 - 确保前端能正常调用API"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Max-Age', '86400')  # 24小时

    # 禁用缓存
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response


# 应用配置
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['JSON_AS_ASCII'] = False  # 支持中文
app.config['JSON_SORT_KEYS'] = False  # 保持原始顺序
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # 禁用缓存


# ============================================
# 🎨 页面/菜单统一配置
# 新增页面时优先只维护这里：
# 1. 在 templates 下新增 xxx.html
# 2. 在 PAGE_CONFIG 中新增一条配置
#    show_menu=True 会自动出现在左侧菜单，同时自动注册 /path 和 /path.html 路由
# ============================================
APP_VERSION = 'v1.2.1'

RELEASE_PROCESS_DATA_FILE = os.path.join(BASE_DIR, 'data', 'release_process_config.json')

PAGE_CONFIG = [
    {'url_path': '/', 'template': 'index', 'title': '首页', 'icon': 'fas fa-home', 'show_menu': True, 'show_home_card': False},
    {'url_path': '/release_process', 'template': 'release_process', 'title': '发布流程配置', 'icon': 'fas fa-clipboard-list', 'show_menu': True, 'description': '编辑并展示域名与发布流程信息', 'color': 'linear-gradient(135deg, #ff9a9e, #fad0c4)'},
    {'url_path': '/encode', 'template': 'encode', 'title': '接口加解密', 'icon': 'fas fa-lock', 'show_menu': True, 'show_home_card': False},
    {'url_path': '/real_name', 'template': 'id_card', 'title': '雷神实名认证查询', 'icon': 'fas fa-id-card', 'show_menu': True, 'description': '实名认证数据加密/解密', 'color': 'linear-gradient(135deg, #667eea, #764ba2)'},
    {'url_path': '/ocpc', 'template': 'ocpc', 'title': 'OCPC查询', 'icon': 'fas fa-database', 'show_menu': True, 'description': 'OCPC 数据查询', 'color': 'linear-gradient(135deg, #00b09b, #96c93d)'},
    {'url_path': '/sdk_decrypt2', 'template': 'sdk_decrypt2', 'title': 'SDK日志解密V2', 'icon': 'fas fa-lock-open', 'show_menu': True, 'description': 'SDK 日志解密 V2', 'color': 'linear-gradient(135deg, #00b09b, #96c93d)'},
    {'url_path': '/qr_code', 'template': 'qr_code', 'title': '二维码生成/解码', 'icon': 'fas fa-qrcode', 'show_menu': True, 'description': '二维码生成和解码工具', 'color': 'linear-gradient(135deg, #2ecc71, #27ae60)'},
    {'url_path': '/ip_query', 'template': 'ip_query', 'title': 'IP地址查询', 'icon': 'fas fa-globe', 'show_menu': True, 'description': '查询 IP 地理位置信息', 'color': 'linear-gradient(135deg, #3498db, #2980b9)'},
    {'url_path': '/document_viewer', 'template': 'document_viewer', 'title': '文档在线查阅', 'icon': 'fas fa-file-alt', 'show_menu': True, 'description': '上传 txt、png、Word 文档在线预览', 'color': 'linear-gradient(135deg, #8e44ad, #3498db)'},
    {'url_path': '/search_referrer', 'template': 'search_referrer', 'title': '搜索来源模拟', 'icon': 'fas fa-search-location', 'show_menu': True, 'description': '模拟不同搜索引擎 document.referrer 来源', 'color': 'linear-gradient(135deg, #1abc9c, #3498db)'},
    {'url_path': '/user_duration', 'template': 'user_duration', 'title': '用户管理', 'icon': 'fas fa-clock', 'show_menu': True, 'description': '管理用户信息', 'color': 'linear-gradient(135deg, #667eea, #764ba2)'},
    {'url_path': '/user_register', 'template': 'user_register', 'title': '账号注册', 'icon': 'fas fa-user-plus', 'show_menu': True, 'description': '批量注册用户账号', 'color': 'linear-gradient(135deg, #ff6b6b, #ffa500)'},

    # 不展示在菜单中，但仍然自动注册路由的页面
    {'url_path': '/sdk_decrypt', 'template': 'sdk_decrypt', 'title': 'SDK日志解密', 'icon': 'fas fa-lock-open', 'show_menu': False},
    {'url_path': '/api-test', 'template': 'api-test', 'title': 'API测试', 'icon': 'fas fa-plug', 'show_menu': False},
    {'url_path': '/documentation', 'template': 'documentation', 'title': '使用文档', 'icon': 'fas fa-book', 'show_menu': False},
    {'url_path': '/about', 'template': 'about', 'title': '关于我们', 'icon': 'fas fa-info-circle', 'show_menu': False},
    {'url_path': '/timestamp', 'template': 'timestamp', 'title': '时间计算器', 'icon': 'fas fa-clock', 'show_menu': False},
    {'url_path': '/user_channel', 'template': 'user_channel', 'title': '用户渠道管理', 'icon': 'fas fa-user-cog', 'show_menu': False},
]

MENU_ITEMS = [
    {
        'href': 'index.html' if item['url_path'] == '/' else f"{item['url_path'].strip('/')}.html",
        'template': item['template'],
        'title': item['title'],
        'icon': item['icon'],
    }
    for item in PAGE_CONFIG
    if item.get('show_menu')
]

HOME_TOOL_CARDS = [
    {
        'href': item.get('card_href') or ('index.html' if item['url_path'] == '/' else f"{item['url_path'].strip('/')}.html"),
        'title': item['title'],
        'icon': item['icon'],
        'description': item.get('description', item['title']),
        'color': item.get('color', 'linear-gradient(135deg, #667eea, #764ba2)'),
    }
    for item in PAGE_CONFIG
    if item.get('show_home_card', item.get('show_menu') and item['url_path'] != '/')
]


# ========== 第2处修改：添加静态文件路由处理 ==========
@app.route('/static/<path:filename>')
def serve_static(filename):
    """自定义静态文件服务路由，确保路径正确"""
    static_dir = os.path.join(BASE_DIR, 'static')

    # 检查文件是否存在
    file_path = os.path.join(static_dir, filename)
    if not os.path.exists(file_path):
        logger.warning(f"静态文件不存在: {file_path}")
        return "File not found", 404

    logger.debug(f"提供静态文件: {filename}")
    return send_from_directory(static_dir, filename)


# ========== 第3处修改：创建模板上下文函数 ==========
@app.context_processor
def inject_template_variables():
    """向所有模板注入变量"""
    return {'static_url': '/static',  # 静态文件URL基础路径
            'debug_mode': config.DEBUG, 'env': config.ENV, 'year': datetime.now().year, 'timestamp': int(time.time()),
            'app_version': APP_VERSION, 'menu_items': MENU_ITEMS, 'home_tool_cards': HOME_TOOL_CARDS
            # 防止缓存
            }


# ============================================
# 🟢 请求频率限制配置
# ============================================
class RateLimiter:
    """请求频率限制器 - 用于防止API滥用"""

    def __init__(self, cleanup_interval: int = 60):
        """
        初始化频率限制器
        
        Args:
            cleanup_interval: 清理过期记录的时间间隔(秒)
        """
        self.request_history = defaultdict(list)
        self.lock = Lock()
        self.cleanup_interval = cleanup_interval
        self.last_cleanup = time.time()

    def is_allowed(self, ip_address: str, limit: int = 2, window: int = 1) -> tuple:
        """
        检查IP是否允许请求
        
        Args:
            ip_address: 客户端IP地址
            limit: 时间窗口内允许的最大请求数
            window: 时间窗口大小(秒)
            
        Returns:
            (是否允许, 需要等待的时间)
        """
        current_time = time.time()

        # 定期清理过期记录
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_expired(window)
            self.last_cleanup = current_time

        with self.lock:
            timestamps = self.request_history[ip_address]
            
            # 移除超出时间窗口的记录
            valid_timestamps = [ts for ts in timestamps if current_time - ts < window]
            self.request_history[ip_address] = valid_timestamps

            # 检查是否超过限制
            if len(valid_timestamps) >= limit:
                oldest_timestamp = min(valid_timestamps)
                remaining_time = window - (current_time - oldest_timestamp)
                return False, max(0, remaining_time)

            # 记录当前请求
            self.request_history[ip_address].append(current_time)
            return True, 0

    def _cleanup_expired(self, window: int):
        """清理过期的请求记录"""
        current_time = time.time()
        with self.lock:
            # 使用字典推导式清理过期记录
            self.request_history = defaultdict(
                list,
                {
                    ip: [ts for ts in timestamps if current_time - ts < window * 2]
                    for ip, timestamps in self.request_history.items()
                    if any(current_time - ts < window * 2 for ts in timestamps)
                }
            )

    def get_stats(self, ip_address: str = None) -> dict:
        """
        获取限制器统计信息
        
        Args:
            ip_address: 要查询的IP地址，为None时返回总体统计
            
        Returns:
            统计信息字典
        """
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
                return {'ip': ip_address, 'message': 'No requests recorded'}
            
            return {
                'total_ips': len(self.request_history),
                'total_requests': sum(len(ts) for ts in self.request_history.values())
            }


# 创建全局频率限制器实例
rate_limiter = RateLimiter()


def get_client_ip() -> str:
    """
    获取客户端真实IP地址
    处理代理和负载均衡的情况
    
    Returns:
        客户端IP地址
    """
    # 优先级: X-Forwarded-For > X-Real-IP > remote_addr
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        ip = request.headers.get('X-Real-IP').strip()
    else:
        ip = request.remote_addr
    return ip or '0.0.0.0'


def apply_rate_limit(limit: int = 2, window: int = 1):
    """
    请求频率限制装饰器
    
    Args:
        limit: 时间窗口内允许的最大请求数
        window: 时间窗口大小(秒)
        
    Returns:
        装饰器函数
        
    Example:
        @app.route('/api/endpoint')
        @apply_rate_limit(limit=5, window=60)  # 每分钟最多5次请求
        def endpoint():
            return jsonify({'data': 'value'})
    """
    def decorator(f):
        from functools import wraps
        
        @wraps(f)
        def wrapper(*args, **kwargs):
            client_ip = get_client_ip()
            allowed, wait_time = rate_limiter.is_allowed(client_ip, limit, window)

            if not allowed:
                logger.warning(
                    f"🚫 请求频率限制 - IP: {client_ip}, "
                    f"路径: {request.path}, 需等待: {wait_time:.2f}秒"
                )
                return jsonify({'success': False, 'error': f'请求过于频繁，请等待 {wait_time:.1f} 秒后重试',
                                'code': 'RATE_LIMIT_EXCEEDED', 'wait_time': wait_time, 'ip': client_ip, 'limit': limit,
                                'window': window,
                                'timestamp': datetime.now().isoformat()}), 429  # 429 Too Many Requests

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

        # 检查目录结构
        logger.info(f"项目根目录: {BASE_DIR}")
        logger.info(f"模板目录: {app.template_folder}")
        logger.info(f"静态文件目录: {app.static_folder}")

        # 确保存储目录存在
        os.makedirs(os.path.dirname(RELEASE_PROCESS_DATA_FILE), exist_ok=True)

        # 检查静态文件目录
        static_dirs = ['css', 'images', 'js']
        for subdir in static_dirs:
            subdir_path = os.path.join(app.static_folder, subdir)
            if os.path.exists(subdir_path):
                logger.info(f"✅ 静态子目录存在: {subdir}")
            else:
                logger.warning(f"⚠️ 静态子目录不存在: {subdir}")

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

    # 全局请求日志和统计
    excluded_paths = ['/static/', '/health', '/favicon.ico']
    if not any(request.path.startswith(path) for path in excluded_paths):
        client_ip = get_client_ip()
        logger.info(f"🌐 请求: {request.method} {request.path} - IP: {client_ip}")


# ========== 通用页面渲染函数（已修复）==========
def render_template_page(page_name):
    """通用页面渲染函数"""
    template_file = f'{page_name}.html'
    template_path = os.path.join(app.template_folder, template_file)

    logger.debug(f"尝试访问页面: {template_file}")
    logger.debug(f"文件路径: {template_path}")

    if os.path.exists(template_path):
        logger.debug(f"✅ 找到 {template_file} 文件")
        try:
            # 添加时间戳参数防止缓存
            timestamp = int(time.time())
            return render_template(template_file, timestamp=timestamp, active_template=page_name)
        except Exception as e:
            logger.error(f"渲染 {page_name} 模板失败: {e}")
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return content
            except Exception as e2:
                logger.error(f"读取 {page_name} 文件失败: {e2}")
                return f"<h1>访问 {page_name} 页面失败: {e2}</h1>", 500
    else:
        logger.warning(f"⚠️ {template_file} 文件不存在: {template_path}")
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>页面未找到 - {page_name}</title>
            <link rel="stylesheet" href="/static/css/common.css">
            <style>
                body {{ font-family: Arial, sans-serif; padding: 40px; text-align: center; background-color: #f5f5f5; }}
                h1 {{ color: #e74c3c; margin-bottom: 20px; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 30px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .btn {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background-color: #3498db; color: white; text-decoration: none; border-radius: 5px; }}
                .btn:hover {{ background-color: #2980b9; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>⚠️ 页面未找到</h1>
                <p>页面 <strong>{template_file}</strong> 不存在</p>
                <p>请确保该文件位于 templates 文件夹中</p>
                <a href="/" class="btn">返回首页</a>
            </div>
        </body>
        </html>
        """, 404


# ============================================
# 🎨 页面路由辅助函数
# ============================================
def register_page_route(url_path: str, template_name: str = None, endpoint: str = None):
    """
    注册页面路由的装饰器工厂
    自动注册带和不带.html后缀的两个路由
    
    Args:
        url_path: URL路径(不带.html)
        template_name: 模板名称(默认与url_path相同)
        endpoint: 端点名称(默认与url_path相同，去掉斜杠和连字符)
        
    Example:
        @register_page_route('/index', 'index', 'index_page')
        def index():
            '''首页'''
            pass
    """
    def decorator(func):
        # 确定模板名称和端点名称
        tpl_name = template_name or url_path.strip('/')
        ep_name = endpoint or url_path.strip('/').replace('-', '_').replace('/', '_')
        
        # 注册不带后缀的路由
        app.add_url_rule(
            url_path,
            endpoint=ep_name,
            view_func=lambda: render_template_page(tpl_name),
            methods=['GET']
        )
        
        # 注册带.html后缀的路由
        html_path = f"{url_path}.html" if not url_path.endswith('/') else f"{url_path}index.html"
        app.add_url_rule(
            html_path,
            endpoint=f"{ep_name}_html",
            view_func=lambda: render_template_page(tpl_name),
            methods=['GET']
        )
        
        return func
    return decorator


# ============================================
# 🎨 页面路由配置
# ============================================
# 页面路由由 PAGE_CONFIG 自动生成，新增页面只需要维护 PAGE_CONFIG 一处。
PAGE_ROUTES = [
    (item['url_path'], item['template'], f"{item['title']}页面")
    for item in PAGE_CONFIG
]

# 批量注册页面路由
for url_path, template_name, description in PAGE_ROUTES:
    # 创建视图函数
    def make_view(tpl_name=template_name, desc=description):
        def view_func():
            f"""
            {desc}
            
            Returns:
                渲染的HTML页面
            """
            return render_template_page(tpl_name)
        view_func.__name__ = f"{tpl_name.replace('-', '_')}_page"
        view_func.__doc__ = desc
        return view_func
    
    # 生成端点名称
    endpoint = template_name.replace('-', '_').replace('/', '_')
    if url_path == '/':
        endpoint = 'index'
    
    # 注册不带.html后缀的路由
    app.add_url_rule(
        url_path,
        endpoint=endpoint,
        view_func=make_view(),
        methods=['GET']
    )
    
    # 注册带.html后缀的路由(首页除外)
    if url_path != '/':
        html_path = f"{url_path}.html"
        app.add_url_rule(
            html_path,
            endpoint=f"{endpoint}_html",
            view_func=make_view(),
            methods=['GET']
        )
    else:
        # 首页特殊处理: /index.html 也指向首页
        app.add_url_rule(
            '/index.html',
            endpoint='index_html',
            view_func=make_view(),
            methods=['GET']
        )


# ========== API接口 ==========
@app.route('/api', methods=['GET'])
@apply_rate_limit(limit=50, window=1)
def api_info():
    """API首页 - 返回JSON信息"""
    db_healthy = db_manager.health_check()
    return jsonify({'service': 'OCPC Query API', 'version': '1.0.0', 'status': 'running', 'environment': config.ENV,
                    'database': {'status': 'connected' if db_healthy else 'disconnected', 'host': config.db_config.host,
                                 'port': config.db_config.port, 'database': config.db_config.database},
                    'endpoints': {'health_check': '/health',
                                  'query_ocpc_mapping': f'{config.API_PREFIX}/query/ocpc-mapping?channel=bytes&order=desc',
                                  'query_ocpc_log': f'{config.API_PREFIX}/query/ocpc-log?channel=360&order=desc',
                                  'batch_query': f'{config.API_PREFIX}/query/batch (POST)',
                                  'rate_limit_stats': '/api/rate-limit-stats'},
                    'timestamp': datetime.now().isoformat()})


# 频率限制统计接口
@app.route('/api/rate-limit-stats', methods=['GET'])
@apply_rate_limit(limit=50, window=1)
def rate_limit_stats():
    """获取频率限制统计信息"""
    ip = request.args.get('ip')
    stats = rate_limiter.get_stats(ip)
    return jsonify({'success': True, 'stats': stats, 'timestamp': datetime.now().isoformat()})


def get_default_release_process_data() -> dict:
    """获取发布流程页默认数据"""
    return {
        'records': [
            {
                'project_name': '',
                'vf_domain': '',
                'production_domain': '',
                'jenkins_process': '',
                'production_process': ''
            }
        ]
    }


def load_release_process_data() -> dict:
    """加载发布流程页配置数据"""
    default_data = get_default_release_process_data()
    try:
        if os.path.exists(RELEASE_PROCESS_DATA_FILE):
            with open(RELEASE_PROCESS_DATA_FILE, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            if isinstance(saved_data, dict):
                # 兼容旧版本单条记录结构
                if 'records' not in saved_data:
                    legacy_record = {
                        'project_name': str(saved_data.get('project_name', '')).strip(),
                        'vf_domain': str(saved_data.get('vf_domain', '')).strip(),
                        'production_domain': str(saved_data.get('production_domain', '')).strip(),
                        'jenkins_process': str(saved_data.get('jenkins_process', '')).strip(),
                        'production_process': str(saved_data.get('production_process', '')).strip()
                    }
                    return {'records': [legacy_record]}

                records = saved_data.get('records', [])
                if isinstance(records, list):
                    normalized_records = []
                    for item in records:
                        if not isinstance(item, dict):
                            continue
                        normalized_records.append({
                            'project_name': str(item.get('project_name', '')).strip(),
                            'vf_domain': str(item.get('vf_domain', '')).strip(),
                            'production_domain': str(item.get('production_domain', '')).strip(),
                            'jenkins_process': str(item.get('jenkins_process', '')).strip(),
                            'production_process': str(item.get('production_process', '')).strip()
                        })
                    return {'records': normalized_records or default_data['records']}
                return {**default_data, **saved_data}
    except Exception as e:
        logger.error(f"加载发布流程配置失败: {e}", exc_info=True)
    return default_data


def save_release_process_data(data: dict):
    """保存发布流程页配置数据"""
    os.makedirs(os.path.dirname(RELEASE_PROCESS_DATA_FILE), exist_ok=True)
    with open(RELEASE_PROCESS_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.route('/api/release-process-config', methods=['GET', 'POST'])
@apply_rate_limit(limit=50, window=1)
def release_process_config():
    """获取或保存发布流程配置"""
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'data': load_release_process_data(),
            'timestamp': datetime.now().isoformat()
        })

    try:
        payload = request.get_json(silent=True) or {}
        incoming_records = payload.get('records', [])

        if not isinstance(incoming_records, list):
            return jsonify({
                'success': False,
                'error': 'records 参数必须为数组',
                'code': 'PARAM_ERROR'
            }), 400

        normalized_records = []
        for item in incoming_records:
            if not isinstance(item, dict):
                continue
            normalized_records.append({
                'project_name': str(item.get('project_name', '')).strip(),
                'vf_domain': str(item.get('vf_domain', '')).strip(),
                'production_domain': str(item.get('production_domain', '')).strip(),
                'jenkins_process': str(item.get('jenkins_process', '')).strip(),
                'production_process': str(item.get('production_process', '')).strip()
            })

        data = {
            'records': normalized_records or get_default_release_process_data()['records']
        }

        save_release_process_data(data)
        return jsonify({
            'success': True,
            'message': '保存成功',
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"保存发布流程配置失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '保存失败',
            'detail': str(e) if config.DEBUG else None,
            'code': 'SAVE_RELEASE_PROCESS_FAILED'
        }), 500


DEFAULT_REAL_NAME_CRYPTO_KEY = os.getenv('REAL_NAME_CRYPTO_KEY', 'id_card')


@app.route(f'{config.API_PREFIX}/real-name/encrypt', methods=['POST'])
@app.route(f'{config.API_PREFIX}/id-card/encrypt', methods=['POST'])
@apply_rate_limit(limit=50, window=1)
def encrypt_id_card_text():
    """
    实名认证文本加密接口。

    Request Body:
        {
            "text": "需要加密的明文",
            "key": "可选，不传则使用服务端内置默认密钥"
        }
    """
    try:
        if IdCardCryptoHandler is None:
            return jsonify({'success': False, 'error': '加解密工具不可用', 'code': 'SERVICE_UNAVAILABLE'}), 500

        data = request.get_json(silent=True) or {}
        plaintext = data.get('text')
        key = data.get('key') or DEFAULT_REAL_NAME_CRYPTO_KEY

        if plaintext is None or plaintext == '':
            return jsonify({'success': False, 'error': 'text 参数不能为空', 'code': 'PARAM_ERROR'}), 400
        if not key:
            return jsonify({'success': False, 'error': 'key 参数不能为空', 'code': 'PARAM_ERROR'}), 400

        handler = IdCardCryptoHandler(key=key)
        encrypted = handler.encrypt(str(plaintext))
        return jsonify({
            'success': True,
            'data': {'encrypted': encrypted},
            'operation': 'real_name_encrypt',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"身份证文本加密失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e), 'code': 'ENCRYPT_ERROR'}), 500


@app.route(f'{config.API_PREFIX}/real-name/decrypt', methods=['POST'])
@app.route(f'{config.API_PREFIX}/id-card/decrypt', methods=['POST'])
@apply_rate_limit(limit=50, window=1)
def decrypt_id_card_text():
    """
    实名认证文本解密接口。

    Request Body:
        {
            "text": "需要解密的 Base64 密文",
            "key": "可选，不传则使用服务端内置默认密钥"
        }
    """
    try:
        if IdCardCryptoHandler is None:
            return jsonify({'success': False, 'error': '加解密工具不可用', 'code': 'SERVICE_UNAVAILABLE'}), 500

        data = request.get_json(silent=True) or {}
        ciphertext = data.get('text')
        key = data.get('key') or DEFAULT_REAL_NAME_CRYPTO_KEY

        if ciphertext is None or ciphertext == '':
            return jsonify({'success': False, 'error': 'text 参数不能为空', 'code': 'PARAM_ERROR'}), 400
        if not key:
            return jsonify({'success': False, 'error': 'key 参数不能为空', 'code': 'PARAM_ERROR'}), 400

        handler = IdCardCryptoHandler(key=key)
        decrypted = handler.decrypt(str(ciphertext).strip())
        return jsonify({
            'success': True,
            'data': {'decrypted': decrypted},
            'operation': 'real_name_decrypt',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"身份证文本解密失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e), 'code': 'DECRYPT_ERROR'}), 400




# ========== OCPC查询API ==========
@app.route(f'{config.API_PREFIX}/query/ocpc-mapping', methods=['GET'])
@apply_rate_limit(limit=50, window=1)
def query_ocpc_mapping():
    """
    查询ocpc_mapping表数据
    
    Query Parameters:
        channel: 渠道名称(必需)
        start_time: 开始时间(可选)
        end_time: 结束时间(可选)
        order: 排序方式(asc/desc, 默认desc)
        page: 页码(默认1)
        page_size: 每页数量(默认20)
        env: 环境(默认production)
    """
    try:
        # 获取查询参数
        params = {
            'channel': request.args.get('channel', 'bytes'),
            'start_time': request.args.get('start_time'),
            'end_time': request.args.get('end_time'),
            'order': request.args.get('order', 'desc'),
            'page': request.args.get('page', 1, type=int),
            'page_size': request.args.get('page_size', config.DEFAULT_PAGE_SIZE, type=int),
            'env': request.args.get('env', config.ENV)
        }
        
        # 执行查询
        result = ocpc_service.query_table(table_name='ocpc_mapping', **params)
        
        # 格式化响应
        response = ocpc_service.format_query_response(
            result=result,
            query_params={
                'channel': params['channel'],
                'start_time': params['start_time'],
                'end_time': params['end_time'],
                'order': params['order'],
                'environment': params['env'],
                'database': config.db_config.database
            },
            rate_limit_info={'applied': True, 'limit': 2, 'window': 1}
        )
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'PARAM_ERROR'
        }), 400
    except Exception as e:
        logger.error(f"查询ocpc_mapping失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '服务器内部错误',
            'code': 'INTERNAL_ERROR',
            'detail': str(e) if config.DEBUG else None
        }), 500


@app.route(f'{config.API_PREFIX}/query/ocpc-log', methods=['GET'])
@apply_rate_limit(limit=50, window=1)
def query_ocpc_log():
    """
    查询ocpc_log表数据
    
    Query Parameters:
        channel: 渠道名称(必需)
        start_time: 开始时间(可选)
        end_time: 结束时间(可选)
        order: 排序方式(asc/desc, 默认desc)
        page: 页码(默认1)
        page_size: 每页数量(默认20)
        env: 环境(默认production)
    """
    try:
        # 获取查询参数
        params = {
            'channel': request.args.get('channel', '360'),
            'start_time': request.args.get('start_time'),
            'end_time': request.args.get('end_time'),
            'order': request.args.get('order', 'desc'),
            'page': request.args.get('page', 1, type=int),
            'page_size': request.args.get('page_size', config.DEFAULT_PAGE_SIZE, type=int),
            'env': request.args.get('env', config.ENV)
        }
        
        # 执行查询
        result = ocpc_service.query_table(table_name='ocpc_log', **params)
        
        # 格式化响应
        response = ocpc_service.format_query_response(
            result=result,
            query_params={
                'channel': params['channel'],
                'start_time': params['start_time'],
                'end_time': params['end_time'],
                'order': params['order'],
                'environment': params['env'],
                'database': config.db_config.database
            },
            rate_limit_info={'applied': True, 'limit': 2, 'window': 1}
        )
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'PARAM_ERROR'
        }), 400
    except Exception as e:
        logger.error(f"查询ocpc_log失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '服务器内部错误',
            'code': 'INTERNAL_ERROR',
            'detail': str(e) if config.DEBUG else None
        }), 500


@app.route(f'{config.API_PREFIX}/query/batch', methods=['POST'])
@apply_rate_limit(limit=50, window=1)
def batch_query():
    """
    批量查询接口
    
    Request Body:
        {
            "queries": [
                {
                    "table": "ocpc_mapping",
                    "channel": "bytes",
                    "start_time": "2024-01-01",
                    "end_time": "2024-01-31",
                    "order": "desc"
                }
            ],
            "env": "production"
        }
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
        
        # 执行批量查询
        results = ocpc_service.batch_query(queries=queries, env=env)
        
        return jsonify({
            'success': True,
            'results': results,
            'environment': env,
            'rate_limit_info': {'applied': True, 'limit': 1, 'window': 2},
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"批量查询失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '服务器内部错误',
            'code': 'INTERNAL_ERROR'
        }), 500


# ========== 用户渠道修改API ==========
@app.route(f'{config.API_PREFIX}/user-channel/update-by-mobile', methods=['POST'])
@apply_rate_limit(limit=50, window=1)
def update_user_channel_by_mobile():
    """
    通过手机号修改用户注册渠道
    
    Request Body:
        {
            "mobile": "手机号",
            "country_code": "国家代码，默认86",
            "new_channel": "新的注册渠道"
        }
    """
    try:
        if not user_channel_service:
            return jsonify({
                'success': False,
                'error': '用户渠道服务不可用',
                'code': 'SERVICE_UNAVAILABLE'
            }), 500
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空',
                'code': 'PARAM_ERROR'
            }), 400
        
        mobile = data.get('mobile')
        country_code = data.get('country_code', '86')
        new_channel = data.get('new_channel')
        
        if not mobile or not new_channel:
            return jsonify({
                'success': False,
                'error': '手机号和新渠道参数不能为空',
                'code': 'PARAM_ERROR'
            }), 400
        
        # 执行更新操作
        result = user_channel_service.update_user_channel_by_mobile(
            mobile=mobile,
            country_code=country_code,
            new_channel=new_channel
        )
        
        # 格式化响应
        response = user_channel_service.format_update_response(
            result=result,
            operation_params={
                'mobile': mobile,
                'country_code': country_code,
                'new_channel': new_channel,
                'operation': 'update_by_mobile'
            }
        )
        
        status_code = 200 if result['success'] else 400
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"通过手机号修改用户渠道失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '服务器内部错误',
            'code': 'INTERNAL_ERROR'
        }), 500


@app.route(f'{config.API_PREFIX}/user-channel/update-by-nn-id', methods=['POST'])
@apply_rate_limit(limit=50, window=1)
def update_user_channel_by_nn_id():
    """
    通过NN ID修改用户注册渠道
    
    Request Body:
        {
            "nn_id": "用户NN ID",
            "new_channel": "新的注册渠道"
        }
    """
    try:
        if not user_channel_service:
            return jsonify({
                'success': False,
                'error': '用户渠道服务不可用',
                'code': 'SERVICE_UNAVAILABLE'
            }), 500
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空',
                'code': 'PARAM_ERROR'
            }), 400
        
        nn_id = data.get('nn_id')
        new_channel = data.get('new_channel')
        
        if not nn_id or not new_channel:
            return jsonify({
                'success': False,
                'error': 'NN ID和新渠道参数不能为空',
                'code': 'PARAM_ERROR'
            }), 400
        
        # 执行更新操作
        result = user_channel_service.update_user_channel(
            nn_id=nn_id,
            new_channel=new_channel
        )
        
        # 格式化响应
        response = user_channel_service.format_update_response(
            result=result,
            operation_params={
                'nn_id': nn_id,
                'new_channel': new_channel,
                'operation': 'update_by_nn_id'
            }
        )
        
        status_code = 200 if result['success'] else 400
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"通过NN ID修改用户渠道失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '服务器内部错误',
            'code': 'INTERNAL_ERROR'
        }), 500


@app.route(f'{config.API_PREFIX}/user-channel/search', methods=['GET'])
@apply_rate_limit(limit=50, window=1)
def search_user():
    """
    通过手机号或NN ID查询用户信息
    
    Query Parameters:
        - mobile: 手机号
        - country_code: 国家代码(默认86)
        - nn_id: NN ID
    """
    try:
        if not user_channel_service:
            return jsonify({
                'success': False,
                'error': '用户渠道服务不可用',
                'code': 'SERVICE_UNAVAILABLE'
            }), 500
        
        mobile = request.args.get('mobile')
        country_code = request.args.get('country_code', '86')
        nn_id = request.args.get('nn_id')
        
        if not mobile and not nn_id:
            return jsonify({
                'success': False,
                'error': '必须提供手机号或NN ID参数',
                'code': 'PARAM_ERROR'
            }), 400
        
        user_info = None
        if mobile:
            user_info = user_channel_service.get_user_by_mobile(mobile, country_code)
        elif nn_id:
            user_info = user_channel_service.get_user_by_nn_id(nn_id)
        
        if user_info:
            return jsonify({
                'success': True,
                'data': user_info,
                'operation': 'search_user',
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
    except Exception as e:
        logger.error(f"查询用户信息失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '服务器内部错误',
            'code': 'INTERNAL_ERROR'
        }), 500


@app.route(f'{config.API_PREFIX}/update_register_time', methods=['POST'])
@apply_rate_limit(limit=50, window=1)
def update_register_time():
    """
    更新用户注册时间
    
    Request Body:
        {
            "user_id": "用户ID",
            "new_create_time": "新的注册时间 (YYYY-MM-DD HH:MM:SS)",
            "account_token": "账户令牌"
        }
    """
    try:
        if not user_channel_service:
            return jsonify({
                'success': False,
                'error': '用户渠道服务不可用',
                'code': 'SERVICE_UNAVAILABLE'
            }), 500
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空',
                'code': 'PARAM_ERROR'
            }), 400
        
        user_id = data.get('user_id')
        new_create_time = data.get('new_create_time')
        account_token = data.get('account_token')
        
        if not user_id or not new_create_time or not account_token:
            return jsonify({
                'success': False,
                'error': '用户ID、新注册时间和账户令牌参数不能为空',
                'code': 'PARAM_ERROR'
            }), 400
        
        # 验证时间格式
        try:
            datetime.strptime(new_create_time, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return jsonify({
                'success': False,
                'error': '时间格式错误，应为 YYYY-MM-DD HH:MM:SS',
                'code': 'PARAM_ERROR'
            }), 400
        
        # 执行更新操作
        result = user_channel_service.update_user_register_time(
            user_id=user_id,
            new_create_time=new_create_time
        )
        
        # 格式化响应
        response = {
            'success': result['success'],
            'message': result['message'],
            'operation': 'update_register_time',
            'timestamp': datetime.now().isoformat(),
            'updated_data': {
                'user_id': user_id,
                'new_create_time': new_create_time
            }
        }
        
        if result['success']:
            logger.info(f"用户注册时间更新成功: user_id={user_id}, new_create_time={new_create_time}")
            return jsonify(response), 200
        else:
            logger.warning(f"用户注册时间更新失败: user_id={user_id}, error={result['message']}")
            return jsonify(response), 400
        
    except Exception as e:
        logger.error(f"更新用户注册时间失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '服务器内部错误',
            'code': 'INTERNAL_ERROR'
        }), 500


@app.route(f'{config.API_PREFIX}/update_payment_status', methods=['POST'])
@apply_rate_limit(limit=50, window=1)
def update_payment_status():
    """
    更新用户付费状态
    
    Request Body:
        {
            "user_id": "用户ID",
            "first_pay_time": "首次付费时间 (YYYY-MM-DD HH:MM:SS 或 null)",
            "account_token": "账户令牌"
        }
    """
    try:
        if not user_channel_service:
            return jsonify({
                'success': False,
                'error': '用户渠道服务不可用',
                'code': 'SERVICE_UNAVAILABLE'
            }), 500
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空',
                'code': 'PARAM_ERROR'
            }), 400
        
        user_id = data.get('user_id')
        # 兼容两种参数名
        first_pay_time = data.get('first_pay_time') or data.get('new_first_pay_time')
        account_token = data.get('account_token')
        
        # 添加调试日志
        logger.info(f"接收到的参数: user_id={user_id}, first_pay_time={first_pay_time}, account_token={account_token}")
        logger.info(f"原始数据: {data}")
        
        if not user_id or not account_token:
            return jsonify({
                'success': False,
                'error': '用户ID和账户令牌参数不能为空',
                'code': 'PARAM_ERROR'
            }), 400
        
        # 验证时间格式（如果提供了时间）
        if first_pay_time is not None and first_pay_time != 'null':
            try:
                # 尝试多种时间格式解析
                parsed_time = None
                
                # 格式1: 标准MySQL格式 YYYY-MM-DD HH:MM:SS
                try:
                    parsed_time = datetime.strptime(first_pay_time, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    pass
                
                # 格式2: ISO格式 YYYY-MM-DDTHH:MM:SS.sssZ
                if parsed_time is None:
                    try:
                        parsed_time = datetime.fromisoformat(first_pay_time.replace('Z', '+00:00'))
                    except ValueError:
                        pass
                
                # 格式3: ISO格式 YYYY-MM-DDTHH:MM:SS
                if parsed_time is None:
                    try:
                        parsed_time = datetime.fromisoformat(first_pay_time)
                    except ValueError:
                        pass
                
                # 如果都没匹配成功，返回错误
                if parsed_time is None:
                    return jsonify({
                        'success': False,
                        'error': f'时间格式错误，支持格式: YYYY-MM-DD HH:MM:SS 或 ISO格式',
                        'received_value': first_pay_time,
                        'code': 'PARAM_ERROR'
                    }), 400
                
                # 统一转换为MySQL格式
                first_pay_time = parsed_time.strftime('%Y-%m-%d %H:%M:%S')
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'时间解析失败: {str(e)}',
                    'received_value': first_pay_time,
                    'code': 'PARAM_ERROR'
                }), 400
        
        # 执行更新操作
        result = user_channel_service.update_user_payment_status(
            user_id=user_id,
            first_pay_time=first_pay_time
        )
        
        # 格式化响应
        response = {
            'success': result['success'],
            'message': result['message'],
            'operation': 'update_payment_status',
            'timestamp': datetime.now().isoformat(),
            'updated_data': {
                'user_id': user_id,
                'first_pay_time': first_pay_time
            }
        }
        
        if result['success']:
            logger.info(f"用户付费状态更新成功: user_id={user_id}, first_pay_time={first_pay_time}")
            return jsonify(response), 200
        else:
            logger.warning(f"用户付费状态更新失败: user_id={user_id}, error={result['message']}")
            return jsonify(response), 400
        
    except Exception as e:
        logger.error(f"更新用户付费状态失败: {str(e)}", exc_info=True)
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
        <link rel="stylesheet" href="/static/css/common.css">
        <style>
            body {{ font-family: Arial, sans-serif; padding: 40px; text-align: center; background-color: #f5f5f5; }}
            h1 {{ color: #e74c3c; margin-bottom: 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 30px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .btn {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background-color: #3498db; color: white; text-decoration: none; border-radius: 5px; }}
            .btn:hover {{ background-color: #2980b9; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>⚠️ 404 - 页面未找到</h1>
            <p>您访问的页面不存在</p>
            <a href="/" class="btn">返回首页</a>
        </div>
    </body>
    </html>
    """, 404


@app.errorhandler(429)
def rate_limit_exceeded(e):
    """处理 429 Too Many Requests 错误"""
    return jsonify({'success': False, 'error': '请求过于频繁，请稍后再试', 'code': 'RATE_LIMIT_EXCEEDED',
                    'timestamp': datetime.now().isoformat(),
                    'message': '为了保护服务器资源，您的请求频率已超过限制'}), 429


# ============================================
# 🎯 二维码解码代理接口 (解决前端 CORS 问题)
# ============================================
import urllib.request
import urllib.parse

@app.route('/api/qr-decode', methods=['GET', 'POST'])
@apply_rate_limit(limit=20, window=60)
def qr_decode():
    """通过图片 URL 或上传文件解码二维码 (服务端代理，绕过 CORS)"""
    logger.info("✅ QR 解码接口被调用!")  # 添加调试日志
    try:
        if request.method == 'GET':
            # 通过 URL 参数解码 - 支持 url 和 file_url 两种参数名
            image_url = request.args.get('url', '') or request.args.get('file_url', '')
            image_url = image_url.strip()
            
            if not image_url:
                return jsonify({'success': False, 'error': '缺少 url 或 file_url 参数'}), 400

            parsed_url = urllib.parse.urlparse(image_url)
            if parsed_url.scheme not in ('http', 'https') or not parsed_url.netloc:
                return jsonify({'success': False, 'error': '图片 URL 格式不正确，仅支持 http/https 网络图片地址'}), 400
            
            # 构造第三方 API 的 URL: file_url 参数必须 URL Encode
            api_url = f"https://api.2dcode.biz/v1/read-qr-code?file_url={urllib.parse.quote(image_url, safe='')}"
            logger.info(f"🔍 请求第三方 API: {api_url}")
            
            # 发起 HTTP GET 请求
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                response_data = resp.read().decode('utf-8')
                data = json.loads(response_data)
            
            contents = data.get('data', {}).get('contents') if isinstance(data.get('data'), dict) else None
            logger.info(f"✅ 解码完成：{contents[0] if contents else '未识别到二维码内容'}")
            return jsonify(data)
            
        elif request.method == 'POST':
            # 通过上传文件解码
            if 'file' not in request.files:
                return jsonify({'success': False, 'error': '缺少 file 字段'}), 400
            
            f = request.files['file']
            file_bytes = f.read()
            
            boundary = b'----FormBoundary7MA4YWxkTrZu0gW'
            content_disposition = f'Content-Disposition: form-data; name="file"; filename="{f.filename}"\r\n'
            content_type_header = f'Content-Type: {f.content_type or "image/png"}\r\n'
            body = (
                b'--' + boundary + b'\r\n' +
                content_disposition.encode() +
                content_type_header.encode() +
                b'\r\n' + file_bytes + b'\r\n' +
                b'--' + boundary + b'--\r\n'
            )
            req = urllib.request.Request(
                'https://api.2dcode.biz/v1/read-qr-code',
                data=body,
                headers={
                    'Content-Type': f'multipart/form-data; boundary={boundary.decode()}',
                    'User-Agent': 'Mozilla/5.0',
                },
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            return jsonify(data)
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8', errors='ignore')
        logger.error(f"QR 解码第三方接口返回错误：HTTP {e.code} {error_body}")
        return jsonify({'success': False, 'error': f'第三方解码接口返回错误：HTTP {e.code}', 'detail': error_body}), 502
    except urllib.error.URLError as e:
        logger.error(f"QR 解码第三方接口连接失败：{e}")
        return jsonify({'success': False, 'error': f'第三方解码接口连接失败：{str(e)}'}), 502
    except json.JSONDecodeError as e:
        logger.error(f"QR 解码响应不是有效 JSON：{e}")
        return jsonify({'success': False, 'error': '第三方解码接口响应格式异常'}), 502
    except Exception as e:
        logger.error(f"QR 解码代理失败：{e}")
        return jsonify({'success': False, 'error': f'请求失败：{str(e)}'}), 500


if __name__ == '__main__':
    print("=" * 80)
    print("🚀 工具箱前端服务启动")
    print("=" * 80)
    print(f"📋 环境: {config.ENV}")
    print(f"🗄️ 数据库: {config.db_config.host}:{config.db_config.port}/{config.db_config.database}")
    print(f"🔗 API前缀: {config.API_PREFIX}")
    print("=" * 80)
    print(f"📁 项目根目录: {BASE_DIR}")
    print(f"📄 模板目录: {app.template_folder}")
    print(f"🎨 静态文件目录: {app.static_folder}")
    print("=" * 80)

    # 检查关键文件
    key_files = [os.path.join(app.template_folder, 'index.html'), os.path.join(app.static_folder, 'css', 'common.css'),
                 os.path.join(app.static_folder, 'images', 'index-logo.png')]

    for file_path in key_files:
        if os.path.exists(file_path):
            print(f"✅ {os.path.basename(file_path)} 文件存在")
        else:
            print(f"❌ {os.path.basename(file_path)} 文件不存在: {file_path}")

    print("=" * 80)
    print("🌐 页面路由:")
    print("  🏠 首页: http://localhost:5000/ 或 http://localhost:5000/index.html")
    print("  🔓 SDK日志解密: http://localhost:5000/sdk-decrypt 或 http://localhost:5000/sdk_decrypt.html")
    print("  📊 频率限制统计: http://localhost:5000/api/rate-limit-stats")
    print("=" * 80)
    print("⚠️ 频率限制配置:")
    print("  🔄 OCPC查询接口: 1秒内最多2次请求")
    print("  🔄 批量查询接口: 2秒内最多1次请求")
    print("  📊 API信息接口: 10秒内最多5次请求")
    print("=" * 80)

    # 手动初始化应用
    initialize_app()
        
    # 检查 QR 解码路由是否注册
    print("=" * 80)
    print("🔍 检查 /api/qr-decode 路由:")
    if '/api/qr-decode' in [str(rule) for rule in app.url_map.iter_rules()]:
        print("✅ /api/qr-decode 路由已注册!")
        print(f"   方法：{[m for m in ['GET', 'POST'] if any(m in str(rule.methods) for rule in app.url_map.iter_rules() if str(rule) == '/api/qr-decode')]}")
    else:
        print("❌ /api/qr-decode 路由未注册!")
        print("   可用路由:", [str(rule) for rule in app.url_map.iter_rules() if 'qr' in str(rule).lower()])
    print("=" * 80)
    
    # 启动 Flask 应用
    app.run(host='0.0.0.0', port=5000, debug=config.DEBUG, threaded=True)
