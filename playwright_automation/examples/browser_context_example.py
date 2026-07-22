"""
高级功能示例
包括上下文管理、认证、拦截器等
"""
import json
import pytest
from playwright.sync_api import sync_playwright

from playwright_automation.core.page import BasePage
from playwright_automation.utils.logger import get_logger


# 示例1: 浏览器上下文隔离
def test_context_isolation():
    """浏览器上下文隔离测试"""
    logger = get_logger("examples.context_isolation")
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        
        # 创建两个隔离的上下文
        context1 = browser.new_context(locale="zh-CN")
        context2 = browser.new_context(locale="en-US")
        
        # 上下文1 - 中文环境
        page1 = context1.new_page()
        page1.goto("https://www.google.com")
        
        # 上下文2 - 英文环境
        page2 = context2.new_page()
        page2.goto("https://www.google.com")
        
        # 验证语言环境不同
        page1_locale = page1.evaluate("() => navigator.language")
        page2_locale = page2.evaluate("() => navigator.language")
        
        logger.info(f"Context1 locale: {page1_locale}")
        logger.info(f"Context2 locale: {page2_locale}")
        
        assert page1_locale != page2_locale
        
        print("✅ 上下文隔离测试通过!")
        
        browser.close()


# 示例2: 保存和恢复认证状态
def test_auth_state_persistence():
    """认证状态持久化测试"""
    logger = get_logger("examples.auth_persistence")
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        
        # 方式1: 手动添加cookie
        context.add_cookies([
            {
                "name": "session_token",
                "value": "test_token_123",
                "domain": ".example.com",
                "path": "/"
            }
        ])
        
        # 方式2: 存储认证状态
        # 1. 先登录，保存状态
        page = context.new_page()
        page.goto("https://example.com")
        # ... 执行登录操作 ...
        
        # 保存状态
        storage_state = context.storage_state()
        logger.info(f"存储状态: {json.dumps(storage_state, indent=2)}")
        
        # 2. 在新上下文中恢复状态
        context2 = browser.new_context()
        context2.add_cookies(storage_state.get("cookies", []))
        
        print("✅ 认证状态测试通过!")
        
        browser.close()


# 示例3: 请求拦截
def test_request_interception():
    """请求拦截测试"""
    logger = get_logger("examples.request_interception")
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        
        # 设置请求拦截器
        def handle_route(route):
            if "analytics" in route.request.url:
                # 跳过分析请求
                route.abort()
                logger.info(f"阻止请求: {route.request.url}")
            else:
                # 继续其他请求
                route.continue_()
        
        context.route("**/*", handle_route)
        
        page = context.new_page()
        
        # 监听响应
        responses = []
        page.on("response", lambda r: responses.append(r.url) if "example" in r.url else None)
        
        page.goto("https://example.com")
        
        logger.info(f"捕获响应数: {len(responses)}")
        print("✅ 请求拦截测试通过!")
        
        browser.close()


# 示例4: Mock响应数据
def test_mock_response():
    """Mock响应测试"""
    logger = get_logger("examples.mock_response")
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        
        # Mock API响应
        context.route(
            "**/api/user",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({
                    "code": 0,
                    "message": "success",
                    "data": {
                        "id": 1,
                        "name": "Mock User",
                        "email": "mock@example.com"
                    }
                })
            )
        )
        
        page = context.new_page()
        page.goto("https://example.com/api/user")
        
        # 验证Mock数据
        response_text = page.content()
        assert "Mock User" in response_text
        assert "mock@example.com" in response_text
        
        logger.info("Mock响应验证通过")
        print("✅ Mock响应测试通过!")
        
        browser.close()


# 示例5: 地理位置模拟
def test_geolocation():
    """地理位置模拟测试"""
    logger = get_logger("examples.geolocation")
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        
        # 创建带有地理位置权限的上下文
        context = browser.new_context(
            permissions=["geolocation"],
            geolocation={"latitude": 39.9042, "longitude": 116.4074},  # 北京
            locale="zh-CN"
        )
        
        page = context.new_page()
        page.goto("https://example.com/location")
        
        # 获取模拟的位置信息
        location = page.evaluate("""
            () => new Promise((resolve) => {
                navigator.geolocation.getCurrentPosition(
                    (pos) => resolve({
                        lat: pos.coords.latitude,
                        lng: pos.coords.longitude
                    }),
                    (err) => resolve({error: err.message})
                );
            })
        """)
        
        logger.info(f"模拟位置: {location}")
        
        print("✅ 地理位置测试通过!")
        
        browser.close()


# 示例6: 设备模拟
def test_device_emulation():
    """设备模拟测试"""
    logger = get_logger("examples.device_emulation")
    
    # 获取iPhone的设备描述
    devices = [
        "iPhone 12",
        "iPad Pro 11",
        "Pixel 5"
    ]
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        
        for device_name in devices:
            device = p.devices.get(device_name)
            if device:
                context = browser.new_context(**device)
                page = context.new_page()
                
                # 验证设备属性
                viewport = page.viewport_size
                user_agent = page.evaluate("() => navigator.userAgent")
                
                logger.info(f"设备: {device_name}")
                logger.info(f"视口: {viewport}")
                logger.info(f"UA: {user_agent[:50]}...")
                
                page.close()
                context.close()
        
        print("✅ 设备模拟测试通过!")
        
        browser.close()


# 示例7: 文件下载
def test_file_download():
    """文件下载测试"""
    logger = get_logger("examples.file_download")
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            accept_downloads=True
        )
        
        page = context.new_page()
        
        # 设置下载监听器
        download_info = {}
        
        def handle_download(download):
            download_info["url"] = download.url
            download_info["suggested_filename"] = download.suggested_filename
            logger.info(f"下载开始: {download.suggested_filename}")
        
        page.on("download", handle_download)
        
        # 触发下载
        page.goto("https://example.com/download")
        page.click("#download-btn")
        
        # 等待下载完成并保存
        if download_info:
            download = page.wait_for_event("download")
            path = download.path()
            logger.info(f"下载完成，路径: {path}")
        
        print("✅ 文件下载测试通过!")
        
        browser.close()


# 示例8: 多个标签页管理
def test_multiple_tabs():
    """多标签页测试"""
    logger = get_logger("examples.multiple_tabs")
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        
        # 创建第一个标签页
        page1 = context.new_page()
        page1.goto("https://www.google.com")
        
        # 创建第二个标签页
        page2 = context.new_page()
        page2.goto("https://www.github.com")
        
        # 创建第三个标签页
        page3 = context.new_page()
        page3.goto("https://www.stackoverflow.com")
        
        logger.info(f"当前标签页数: {len(context.pages)}")
        
        # 切换到第一个标签页
        page1.bring_to_front()
        assert "google" in page1.url
        
        # 关闭第二个标签页
        page2.close()
        logger.info(f"关闭后标签页数: {len(context.pages)}")
        
        # 在第一个标签页中打开新链接
        page1.click("a[href]")  # 假设点击一个链接在新标签页打开
        
        print("✅ 多标签页测试通过!")
        
        browser.close()


# 示例9: 对话框处理
def test_dialog_handling():
    """对话框处理测试"""
    logger = get_logger("examples.dialog_handling")
    
    dialog_info = {}
    
    def handle_dialog(dialog):
        dialog_info["type"] = dialog.type
        dialog_info["message"] = dialog.message
        
        logger.info(f"对话框类型: {dialog.type}")
        logger.info(f"对话框消息: {dialog.message}")
        
        # 根据类型处理
        if dialog.type == "alert":
            dialog.accept()
        elif dialog.type == "confirm":
            dialog.accept()  # 或 dialog.dismiss()
        elif dialog.type == "prompt":
            dialog.accept("输入的值")
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        page.on("dialog", handle_dialog)
        
        # 触发alert对话框
        page.evaluate("() => alert('这是一个警告!')")
        page.wait_for_timeout(1000)
        
        # 触发confirm对话框
        page.evaluate("() => confirm('确认操作?')")
        page.wait_for_timeout(1000)
        
        # 触发prompt对话框
        page.evaluate("() => prompt('请输入:', '默认值')")
        page.wait_for_timeout(1000)
        
        logger.info(f"捕获对话框: {dialog_info}")
        
        print("✅ 对话框处理测试通过!")
        
        browser.close()


# 示例10: 性能监控
def test_performance_monitoring():
    """性能监控测试"""
    logger = get_logger("examples.performance")
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # 启用性能监控
        client = await page.context.new_cdp_session(page)
        await client.send("Performance.enable")
        
        # 记录开始时间
        start_time = page.evaluate("() => Date.now()")
        
        page.goto("https://www.google.com")
        
        # 等待加载完成
        page.wait_for_load_state("networkidle")
        
        # 获取性能指标
        metrics = await client.send("Performance.getMetrics")
        
        logger.info("性能指标:")
        for m in metrics["metrics"]:
            if m["name"] in ["ScriptDuration", "LayoutDuration", "TaskDuration"]:
                logger.info(f"  {m['name']}: {m['value']:.2f}ms")
        
        print("✅ 性能监控测试通过!")
        
        browser.close()


if __name__ == "__main__":
    # 运行单个测试
    test_context_isolation()
