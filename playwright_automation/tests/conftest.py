"""
Pytest配置文件
提供Playwright测试的fixtures和钩子
"""
import os
import sys
import time
import pytest
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright, Page
from playwright_automation.core.browser import BrowserManager, browser_manager
from playwright_automation.utils.logger import setup_logger, TestLogger


# ========== Fixtures ==========

@pytest.fixture(scope="session")
def playwright():
    """Playwright会话级fixture"""
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright):
    """浏览器会话级fixture"""
    browser_manager.start()
    browser = browser_manager.launch_browser()
    yield browser
    browser_manager.close_all()
    browser_manager.stop()


@pytest.fixture(scope="function")
def context(browser):
    """浏览器上下文（函数级）"""
    context = browser_manager.create_context(context_id=f"context_{int(time.time() * 1000)}")
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context):
    """页面fixture"""
    page = context.new_page()
    # 设置默认超时
    page.set_default_timeout(30000)
    yield page
    page.close()


@pytest.fixture(scope="function")
def base_page(page):
    """基础页面对象"""
    from playwright_automation.core.page import BasePage
    return BasePage(page)


@pytest.fixture(scope="session")
def logger():
    """日志fixture"""
    return setup_logger("test_execution")


# ========== 钩子函数 ==========

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_makereport(item, call):
    """在测试运行时生成报告"""
    if call.when == "call":
        # 获取测试结果
        outcome = call.excinfo
        if outcome is None:
            status = "PASSED"
        else:
            status = "FAILED"
        
        # 获取页面对象进行截图
        if hasattr(item, 'funcargs') and 'page' in item.funcargs:
            page = item.funcargs['page']
            if status == "FAILED" and settings.report.screenshot_on_failure:
                try:
                    screenshot_dir = Path("reports/screenshots")
                    screenshot_dir.mkdir(parents=True, exist_ok=True)
                    screenshot_path = screenshot_dir / f"{item.name}_{int(time.time())}.png"
                    page.screenshot(path=str(screenshot_path))
                    TestLogger.log_screenshot(str(screenshot_path), f"测试失败: {item.name}")
                except Exception as e:
                    logging.error(f"截图失败: {e}")


def pytest_configure(config):
    """Pytest配置钩子"""
    # 加载配置
    from playwright_automation.config.settings import settings
    
    # 创建必要的目录
    Path("reports/screenshots").mkdir(parents=True, exist_ok=True)
    Path("reports/videos").mkdir(parents=True, exist_ok=True)
    Path("reports/traces").mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(parents=True, exist_ok=True)


def pytest_collection_modifyitems(config, items):
    """修改测试收集项"""
    for item in items:
        # 为所有测试添加标记
        if "smoke" not in item.keywords:
            item.add_marker(pytest.mark.smoke)
        if "regression" not in item.keywords:
            item.add_marker(pytest.mark.regression)


# ========== 辅助函数 ==========

def get_element_screenshot(page: Page, selector: str, path: str):
    """获取元素截图"""
    try:
        loc = page.locator(selector)
        loc.screenshot(path=path)
    except Exception as e:
        logging.error(f"元素截图失败: {e}")


def save_page_state(page: Page, name: str):
    """保存页面状态"""
    state = {
        "url": page.url,
        "title": page.title(),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    state_file = Path(f"reports/page_states/{name}.json")
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ========== Pytest标记 ==========

def pytest_configure(config):
    """注册自定义标记"""
    config.addinivalue_line("markers", "smoke: 冒烟测试")
    config.addinivalue_line("markers", "regression: 回归测试")
    config.addinivalue_line("markers", "ui: UI测试")
    config.addinivalue_line("markers", "api: API测试")
    config.addinivalue_line("markers", "slow: 慢速测试")
