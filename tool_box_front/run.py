#!/usr/bin/env python
"""
OCPC Query API 启动脚本
"""
import os
import sys
# import webbrowser
# import threading
import time

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# def open_browser():
#     """延迟打开浏览器"""
#     time.sleep(2)  # 等待服务器启动
#     webbrowser.open('http://localhost:5000')


if __name__ == '__main__':

    from app import app
    # 仅新增这2行！解决静态文件异常+中文接口乱码
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # 禁用静态文件缓存
    app.config['JSON_AS_ASCII'] = False          # 接口中文不转义
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True,
        use_reloader=False  # 禁用reloader以避免重复启动
    )