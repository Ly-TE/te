"""
统一 Token 管理服务
负责管理后台登录 token 的获取、缓存、续期等操作
"""
import logging
import time
import warnings
from datetime import datetime, timedelta
from threading import Lock
import requests
import json

# 禁用 SSL 警告
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

logger = logging.getLogger(__name__)

class TokenService:
    """统一Token管理服务"""
    
    def __init__(self):
        self.tokens = {}  # 存储token信息 {client_ip: {token, expiry_time, last_used}}
        self.shared_token = None  # 共享的token信息 {token, expiry_time, created_at}
        self.lock = Lock()
        self.default_account = {
            'phone': '19900000000',
            'smscode': '1'
        }
        
    def get_or_refresh_token(self, client_ip):
        """
        获取有效token，如果过期则自动刷新
        使用共享token机制，避免不同IP互相挤掉
        通过实际API调用验证token有效性
        
        Args:
            client_ip (str): 客户端IP地址
            
        Returns:
            dict: {'token': str, 'expiry_time': str, 'is_new': bool}
        """
        with self.lock:
            # 首先检查共享token是否有效
            if self.shared_token:
                if self._is_shared_token_valid():
                    logger.debug(f"使用共享token给客户端 {client_ip}")
                    return {
                        'token': self.shared_token['token'],
                        'expiry_time': self.shared_token['expiry_time'],
                        'is_new': False
                    }
                else:
                    logger.info("共享token已失效，需要获取新token")
                    # 清除失效的共享token和所有缓存记录
                    self.shared_token = None
                    self.tokens.clear()
                    logger.info("已清除所有缓存的token记录")
            
            # 检查该IP是否已有独立token
            if client_ip in self.tokens:
                token_info = self.tokens[client_ip]
                # 更新最后使用时间
                token_info['last_used'] = datetime.now().isoformat()
                logger.debug(f"返回缓存的token给客户端 {client_ip}")
                # 同步到共享token
                self.shared_token = {
                    'token': token_info['token'],
                    'expiry_time': token_info['expiry_time'],
                    'created_at': token_info.get('created_at', datetime.now().isoformat())
                }
                return {
                    'token': token_info['token'],
                    'expiry_time': token_info['expiry_time'],
                    'is_new': False
                }
            
            # 获取新token
            logger.info(f"为客户端 {client_ip} 获取新token")
            new_token_info = self._fetch_new_token()
            
            if new_token_info:
                # 更新共享token
                self.shared_token = {
                    'token': new_token_info['token'],
                    'expiry_time': new_token_info['expiry_time'],
                    'created_at': datetime.now().isoformat()
                }
                
                # 同时缓存到该IP的独立记录
                self.tokens[client_ip] = {
                    'token': new_token_info['token'],
                    'expiry_time': new_token_info['expiry_time'],
                    'last_used': datetime.now().isoformat(),
                    'created_at': datetime.now().isoformat()
                }
                
                # 清理过期的token记录
                self._cleanup_expired_tokens()
                
                return {
                    'token': new_token_info['token'],
                    'expiry_time': new_token_info['expiry_time'],
                    'is_new': True
                }
            else:
                return None
    
    def _fetch_new_token(self):
        """
        调用现有登录接口获取新token
        
        Returns:
            dict: {'token': str, 'expiry_time': str} 或 None
        """
        try:
            url = 'https://vf-staffapi.leigod.com/staff/login/code'
            
            payload = {
                'phone': self.default_account['phone'],
                'smscode': self.default_account['smscode'],
                'smscode_key': ''
            }
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            logger.debug(f"调用登录接口：{url}")
            response = requests.post(url, json=payload, headers=headers, timeout=10, verify=False)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') == 0 and data.get('data') and data['data'].get('login_info'):
                login_info = data['data']['login_info']
                token = login_info.get('account_token')
                expiry_time = login_info.get('expiry_time')
                
                if token and expiry_time:
                    logger.info(f"成功获取新token，有效期至: {expiry_time}")
                    return {
                        'token': token,
                        'expiry_time': expiry_time
                    }
                else:
                    logger.error("登录接口返回数据缺少必要字段")
                    return None
            else:
                logger.error(f"登录接口调用失败: {data.get('msg', '未知错误')}")
                return None
                
        except Exception as e:
            logger.error(f"获取token时发生异常: {e}")
            return None
    
    def _is_shared_token_valid(self):
        """
        通过实际API调用验证共享token是否有效
        
        Returns:
            bool: token是否有效
        """
        if not self.shared_token:
            return False
            
        try:
            # 使用共享 token 调用 member 接口进行验证
            test_url = f"https://vf-staffapi.leigod.com/staff/member?account_token={self.shared_token['token']}&size=1&page=1&search=id__equal__1"
                        
            response = requests.get(test_url, timeout=5, verify=False)
            data = response.json()
            
            # 如果返回400006错误，说明token已失效
            if data.get('code') == 400006:
                logger.info("共享token验证失败，token已失效")
                return False
            else:
                logger.debug("共享token验证通过")
                return True
                
        except Exception as e:
            logger.error(f"验证共享token时发生异常: {e}")
            return False
    
    def _is_token_expired(self, expiry_time_str):
        """
        检查token是否过期（通过实际API调用来验证）
        
        Args:
            expiry_time_str (str): 过期时间字符串（仅作标识，不用于判断）
            
        Returns:
            bool: 是否过期
        """
        # 不再基于时间判断，总是返回False
        # 实际过期验证将在API调用时进行
        return False
    
    def _cleanup_expired_tokens(self):
        """清理过期的token记录"""
        current_time = datetime.now()
        expired_clients = []
        
        for client_ip, token_info in self.tokens.items():
            try:
                last_used = datetime.fromisoformat(token_info['last_used'])
                # 如果超过1小时未使用，则清理
                if current_time - last_used > timedelta(hours=1):
                    expired_clients.append(client_ip)
            except Exception as e:
                logger.error(f"清理token时解析时间失败: {e}")
                expired_clients.append(client_ip)
        
        for client_ip in expired_clients:
            del self.tokens[client_ip]
            logger.debug(f"清理过期token记录: {client_ip}")
    
    def get_token_stats(self):
        """
        获取token统计信息
        
        Returns:
            dict: 统计信息
        """
        with self.lock:
            active_tokens = len([t for t in self.tokens.values() 
                               if not self._is_token_expired(t['expiry_time'])])
            
            return {
                'total_clients': len(self.tokens),
                'active_tokens': active_tokens,
                'expired_tokens': len(self.tokens) - active_tokens
            }

# 全局实例
token_service = TokenService()