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
    # 在后台线程中打开浏览器
    # browser_thread = threading.Thread(target=open_browser)
    # browser_thread.daemon = True
    # browser_thread.start()

    # 导入并运行应用
    from app import app

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True,
        use_reloader=False  # 禁用reloader以避免重复启动
    )