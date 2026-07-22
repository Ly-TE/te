"""
Google搜索自动化示例
展示如何使用Playwright自动化框架进行Web操作
"""
import time
import pytest
from playwright.sync_api import sync_playwright, Page, expect

from playwright_automation.core.browser import BrowserManager
from playwright_automation.core.page import BasePage
from playwright_automation.utils.logger import get_logger


# 示例1: 基础Google搜索
def test_google_search_basic():
    """基础Google搜索测试"""
    logger = get_logger("examples.google_search")
    
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        try:
            logger.info("开始Google搜索测试")
            
            # 导航到Google
            page.goto("https://www.google.com")
            logger.info("已打开Google首页")
            
            # 等待搜索框加载
            page.wait_for_selector("[name='q']", timeout=10000)
            
            # 输入搜索关键词
            page.fill("[name='q']", "Playwright Python")
            logger.info("已输入搜索关键词")
            
            # 点击搜索按钮
            page.click("[name='btnK']")
            logger.info("已点击搜索按钮")
            
            # 等待搜索结果加载
            page.wait_for_selector("#search", timeout=10000)
            
            # 获取搜索结果数量
            results = page.locator("#search .g").all()
            logger.info(f"找到 {len(results)} 条搜索结果")
            
            # 验证结果
            assert len(results) > 0, "应该有搜索结果"
            
            # 获取第一个结果标题
            first_result_title = page.locator("#search h3").first.text_content()
            logger.info(f"第一个结果标题: {first_result_title}")
            
            print(f"✅ 测试通过! 找到 {len(results)} 条结果")
            
        except Exception as e:
            logger.error(f"测试失败: {e}")
            # 截图保存
            page.screenshot(path="reports/screenshots/google_search_failed.png")
            raise
        
        finally:
            browser.close()


# 示例2: 使用BasePage类
def test_google_search_with_base_page():
    """使用BasePage类的Google搜索测试"""
    logger = get_logger("examples.google_search_base_page")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # 创建BasePage实例
            base_page = BasePage(page)
            
            # 导航
            base_page.goto("https://www.google.com")
            
            # 等待并操作
            base_page.wait_for_selector("[name='q']", timeout=10)
            base_page.fill("[name='q']", "Selenium vs Playwright")
            
            # 点击搜索
            base_page.click("[name='btnK']")
            
            # 等待结果
            base_page.wait_for_selector("#search", timeout=10)
            
            # 验证
            assert base_page.is_visible("#search .g")
            
            # 获取标题
            title = base_page.title
            assert "Selenium vs Playwright" in title
            
            print("✅ BasePage测试通过!")
            
        finally:
            browser.close()


# 示例3: 高级搜索功能
def test_google_advanced_search():
    """高级搜索功能测试"""
    logger = get_logger("examples.google_advanced_search")
    
    search_keywords = [
        "Python自动化测试",
        "Playwright vs Cypress",
        "Web UI自动化"
    ]
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(locale="zh-CN")
        page = context.new_page()
        
        try:
            page.goto("https://www.google.com")
            
            for keyword in search_keywords:
                logger.info(f"搜索: {keyword}")
                
                # 清空并输入
                page.fill("[name='q']", "")
                page.fill("[name='q']", keyword)
                page.press("[name='q']", "Enter")
                
                # 等待结果
                page.wait_for_selector("#search", timeout=10000)
                
                # 获取结果统计
                result_count = page.locator("#search .g").count()
                logger.info(f"关键词 '{keyword}' 找到 {result_count} 条结果")
                
                assert result_count > 0
            
            print("✅ 高级搜索测试通过!")
            
        finally:
            browser.close()


# 示例4: 搜索结果分页
def test_google_search_pagination():
    """搜索结果分页测试"""
    logger = get_logger("examples.google_pagination")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # 搜索
            page.goto("https://www.google.com")
            page.fill("[name='q']", "Python programming")
            page.click("[name='btnK']")
            page.wait_for_selector("#search", timeout=10000)
            
            # 获取第一页结果
            first_page_results = page.locator("#search .g").all()
            logger.info(f"第一页有 {len(first_page_results)} 条结果")
            
            # 记录第一个结果的标题
            first_title_1 = page.locator("#search h3").first.text_content()
            
            # 点击下一页
            page.click("#pnnext")
            page.wait_for_load_state("networkidle", timeout=10000)
            
            # 获取第二页结果
            second_page_results = page.locator("#search .g").all()
            logger.info(f"第二页有 {len(second_page_results)} 条结果")
            
            # 验证结果不同
            first_title_2 = page.locator("#search h3").first.text_content()
            assert first_title_1 != first_title_2, "分页结果应该不同"
            
            print("✅ 分页测试通过!")
            
        finally:
            browser.close()


# 示例5: 错误处理和重试
def test_google_search_with_retry():
    """带重试的搜索测试"""
    logger = get_logger("examples.google_retry")
    
    max_attempts = 3
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"尝试 {attempt}/{max_attempts}")
                
                page.goto("https://www.google.com", timeout=5000)
                page.fill("[name='q']", "Playwright")
                page.click("[name='btnK']")
                page.wait_for_selector("#search", timeout=10000)
                
                results = page.locator("#search .g").count()
                assert results > 0
                
                print(f"✅ 重试测试成功 (尝试 {attempt})")
                break
                
            except Exception as e:
                logger.error(f"尝试 {attempt} 失败: {e}")
                if attempt == max_attempts:
                    raise
                time.sleep(1)
            
            finally:
                browser.close()


# 示例6: 性能测试
def test_google_search_performance():
    """搜索性能测试"""
    logger = get_logger("examples.google_performance")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # 测量页面加载时间
            start_time = time.time()
            
            page.goto("https://www.google.com")
            page.wait_for_selector("[name='q']", timeout=10000)
            
            page_load_time = time.time() - start_time
            logger.info(f"页面加载时间: {page_load_time:.2f}秒")
            
            # 测量搜索时间
            start_time = time.time()
            
            page.fill("[name='q']", "Python")
            page.click("[name='btnK']")
            page.wait_for_selector("#search", timeout=10000)
            
            search_time = time.time() - start_time
            logger.info(f"搜索响应时间: {search_time:.2f}秒")
            
            # 断言性能要求
            assert page_load_time < 3, f"页面加载时间应小于3秒，实际: {page_load_time:.2f}秒"
            assert search_time < 2, f"搜索响应时间应小于2秒，实际: {search_time:.2f}秒"
            
            print(f"✅ 性能测试通过! 页面加载: {page_load_time:.2f}s, 搜索: {search_time:.2f}s")
            
        finally:
            browser.close()


if __name__ == "__main__":
    # 运行单个测试
    test_google_search_basic()
