#!/usr/bin/env python
"""
OCPC Query API 启动脚本
"""
import os
import sys

import time

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))





if __name__ == '__main__':

    from app import app
    # 缓存控制配置
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # 禁用静态文件缓存
    app.config['JSON_AS_ASCII'] = False          # 接口中文不转义
    
    # 添加额外的缓存控制头
    @app.after_request
    def after_request(response):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True,
        use_reloader=False  # 禁用reloader以避免重复启动
    )