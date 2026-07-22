"""
Playwright Automation Framework
基于Playwright的Python浏览器自动化测试框架

提供简洁、强大的API来构建Web自动化测试、爬虫和RPA流程
"""

__version__ = "1.0.0"
__author__ = "Playwright Automation Team"

# 核心模块
from .core.browser import BrowserManager, browser_manager
from .core.page import BasePage, PageManager
from .core.element import ElementHandler

# 配置模块
from .config.settings import Settings, settings
from .config.locators import Locators, Locator

# 工具模块
from .utils.assertions import AssertHelper, Assertions, WaitFor
from .utils.logger import setup_logger, get_logger, TestLogger
from .utils.helpers import (
    wait_for_condition,
    retry,
    capture_debug_info,
    generate_random_string,
    generate_random_email,
    generate_random_phone,
    Timer
)

# 公开API
__all__ = [
    # 版本信息
    "__version__",
    
    # 核心组件
    "BrowserManager",
    "browser_manager",
    "BasePage",
    "PageManager",
    "ElementHandler",
    
    # 配置
    "Settings",
    "settings",
    "Locators",
    "Locator",
    
    # 断言
    "AssertHelper",
    "Assertions",
    "WaitFor",
    
    # 日志
    "setup_logger",
    "get_logger",
    "TestLogger",
    
    # 工具函数
    "wait_for_condition",
    "retry",
    "capture_debug_info",
    "generate_random_string",
    "generate_random_email",
    "generate_random_phone",
    "Timer",
]


def quick_start():
    """
    快速启动示例
    
    使用方法:
        from playwright_automation import quick_start
        
        # 创建浏览器
        browser = quick_start()
        
        # 导航到网站
        page = browser.new_page()
        page.goto("https://example.com")
        
        # 执行操作...
        page.click("#button")
        page.fill("#input", "text")
        
        # 关闭
        browser.close()
    """
    from playwright.sync_api import sync_playwright
    
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=False)
    return browser
