"""
统一登录API接口
提供统一的token获取和管理接口
"""
from flask import Blueprint, request, jsonify
import logging
from datetime import datetime

from services.token_service import token_service

logger = logging.getLogger(__name__)

# 创建蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/token', methods=['GET', 'POST'])
def get_token():
    """
    获取管理后台访问token
    客户端通过此接口获取有效的account_token
    
    Supports both GET and POST methods for backward compatibility.
    
    For POST requests, accepts optional JSON body with account info.
    
    Returns:
        JSON: {
            'success': bool,
            'token': str,
            'expiry_time': str,
            'is_new': bool,
            'message': str
        }
    """
    try:
        # 获取客户端IP
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        logger.info(f"客户端 {client_ip} 请求获取token (Method: {request.method})")
        
        # 如果是POST请求，可以接受额外的参数（例如账户信息）
        if request.method == 'POST':
            try:
                data = request.get_json(silent=True)
                if data:
                    # 可以在这里处理POST数据，比如自定义账户信息
                    phone = data.get('phone', '19900000000')  # 默认电话
                    smscode = data.get('smscode', '1')  # 默认验证码
                    logger.info(f"POST请求包含自定义账户信息: phone={phone}")
            except Exception as e:
                logger.warning(f"解析POST数据失败: {e}")
        
        # 获取或刷新token
        token_result = token_service.get_or_refresh_token(client_ip)
        
        if token_result:
            return jsonify({
                'success': True,
                'token': token_result['token'],
                'expiry_time': token_result['expiry_time'],
                'is_new': token_result['is_new'],
                'message': 'Token获取成功' if token_result['is_new'] else '返回缓存的Token'
            })
        else:
            return jsonify({
                'success': False,
                'token': None,
                'message': '获取Token失败，请稍后重试'
            }), 500
            
    except Exception as e:
        logger.error(f"获取token时发生异常: {e}")
        return jsonify({
            'success': False,
            'token': None,
            'message': f'服务器内部错误: {str(e)}'
        }), 500

@auth_bp.route('/token/validate', methods=['GET'])
def validate_token():
    """
    验证token有效性（轻量级探针）
    
    Returns:
        JSON: {
            'success': bool,
            'valid': bool,
            'message': str
        }
    """
    try:
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        # 简单检查是否有缓存的token
        with token_service.lock:
            has_token = client_ip in token_service.tokens
            if has_token:
                token_info = token_service.tokens[client_ip]
                is_valid = not token_service._is_token_expired(token_info['expiry_time'])
            else:
                is_valid = False
        
        return jsonify({
            'success': True,
            'valid': is_valid,
            'message': 'Token有效' if is_valid else 'Token无效或不存在'
        })
        
    except Exception as e:
        logger.error(f"验证token时发生异常: {e}")
        return jsonify({
            'success': False,
            'valid': False,
            'message': f'验证失败: {str(e)}'
        }), 500

@auth_bp.route('/stats', methods=['GET'])
def get_token_stats():
    """
    获取token服务统计信息（管理员接口）
    
    Returns:
        JSON: {
            'success': bool,
            'stats': dict,
            'timestamp': str
        }
    """
    try:
        stats = token_service.get_token_stats()
        return jsonify({
            'success': True,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取统计信息时发生异常: {e}")
        return jsonify({
            'success': False,
            'stats': None,
            'message': f'获取统计信息失败: {str(e)}'
        }), 500

@auth_bp.route('/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    
    Returns:
        JSON: {
            'status': str,
            'service': str,
            'timestamp': str
        }
    """
    return jsonify({
        'status': 'healthy',
        'service': 'Token Management Service',
        'timestamp': datetime.now().isoformat()
    })