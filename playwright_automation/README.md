# Playwright Automation Framework

基于 Playwright 的 Python 浏览器自动化框架，提供简洁、强大的 API 来构建 Web 自动化测试、爬虫和 RPA 流程。

## 📋 目录

- [特性](#-特性)
- [安装](#-安装)
- [快速开始](#-快速开始)
- [框架结构](#-框架结构)
- [使用示例](#-使用示例)
- [API文档](#api文档)
- [最佳实践](#-最佳实践)
- [测试运行](#-测试运行)

## ✨ 特性

- 🚀 **简洁的API** - 封装了复杂的Playwright API，提供更易用的接口
- 🔧 **配置管理** - 支持多环境配置，灵活的配置选项
- 📊 **完整日志** - 详细的日志记录和报告生成
- 🧩 **模块化设计** - 清晰的模块划分，易于扩展
- 🧪 **Pytest集成** - 完整的pytest fixture支持
- 📝 **丰富示例** - 包含Google搜索、表单自动化等多个示例
- ⏱️ **智能等待** - 内置多种等待和重试机制
- 📷 **自动截图** - 测试失败时自动截图

## 📦 安装

### 依赖要求

- Python 3.8+
- Playwright

### 安装步骤

```bash
# 1. 安装核心依赖
pip install playwright
pip install pytest
pip install python-dotenv
pip install PyYAML

# 2. 安装浏览器
playwright install chromium  # 或 firefox, webkit

# 3. (可选) 安装所有浏览器
playwright install
```

## 🚀 快速开始

### 基础使用

```python
from playwright.sync_api import sync_playwright
from playwright_automation import BrowserManager

# 使用 BrowserManager
browser_mgr = BrowserManager()
browser_mgr.start()
browser = browser_mgr.launch_browser(headless=False)

page = browser.new_page()
page.goto("https://www.google.com")

# 执行操作
page.fill("[name='q']", "Playwright Python")
page.click("[name='btnK']")

# 关闭
browser.close()
browser_mgr.stop()
```

### 使用 BasePage

```python
from playwright_automation.core.page import BasePage

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    
    # 创建BasePage实例
    base_page = BasePage(page, url="https://www.google.com")
    
    # 导航
    base_page.goto()
    
    # 操作元素
    base_page.fill("[name='q']", "Hello Playwright")
    base_page.click("[name='btnK']")
    
    # 断言
    assert base_page.is_visible("#search")
```

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_example.py

# 运行带标记的测试
pytest -m smoke

# 生成报告
pytest tests/ --alluredir=reports/allure-results
```

## 📁 框架结构

```
playwright_automation/
├── __init__.py                 # 框架入口
├── config/                     # 配置模块
│   ├── __init__.py
│   ├── settings.py            # 全局配置
│   └── locators.py            # 元素定位器
├── core/                      # 核心模块
│   ├── __init__.py
│   ├── browser.py             # 浏览器管理
│   ├── page.py               # 页面基类
│   └── element.py            # 元素处理
├── utils/                    # 工具模块
│   ├── __init__.py
│   ├── assertions.py         # 断言工具
│   ├── logger.py             # 日志工具
│   └── helpers.py            # 辅助函数
├── tests/                    # 测试目录
│   ├── __init__.py
│   └── conftest.py           # Pytest配置
└── examples/                 # 示例代码
    ├── google_search_example.py
    └── form_automation_example.py
```

## 📖 使用示例

### 示例1: Google搜索

```python
from playwright.sync_api import sync_playwright
from playwright_automation import BasePage

def test_google_search():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        base_page = BasePage(page)
        
        # 导航
        base_page.goto("https://www.google.com")
        
        # 搜索
        base_page.fill("[name='q']", "Playwright Python")
        base_page.click("[name='btnK']")
        
        # 验证
        base_page.wait_for_selector("#search")
        assert base_page.is_visible("#search .g")
        
        browser.close()
```

### 示例2: 表单操作

```python
def test_form_operations():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        base_page = BasePage(page)
        
        # 导航到表单页面
        base_page.goto("https://example.com/form")
        
        # 填写表单
        base_page.fill("#username", "testuser")
        base_page.fill("#email", "test@example.com")
        base_page.fill("#password", "password123")
        
        # 选择选项
        base_page.select_option("#country", "China")
        
        # 勾选复选框
        base_page.check("#agree-terms")
        
        # 提交
        base_page.click("#submit-btn")
        
        # 验证
        assert base_page.is_visible(".success-message")
        
        browser.close()
```

### 示例3: 使用断言

```python
from playwright_automation import Assertions

def test_with_assertions():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        assertions = Assertions(page)
        
        page.goto("https://example.com")
        
        # URL断言
        assertions.url_contains("example.com")
        assertions.url_matches(r"https://.*\.example\.com/.*")
        
        # 标题断言
        assertions.title_contains("Example")
        
        # 元素断言
        assertions.element_visible("#main-content")
        assertions.element_text_contains("#title", "Welcome")
        assertions.element_enabled("#submit-btn")
        
        browser.close()
```

### 示例4: 智能等待和重试

```python
from playwright_automation.utils.helpers import retry, wait_for_condition

# 使用重试装饰器
@retry(max_attempts=3, delay=1)
def click_and_wait():
    page.click("#dynamic-button")
    wait_for_condition(lambda: page.is_visible("#result"), timeout=10)
    return True

# 使用ElementHandler
from playwright_automation.core.element import ElementHandler

handler = ElementHandler(page)
handler.retry_click("#unstable-button", max_retries=5)
handler.smart_wait("#content-loaded", state="visible")
```

## API文档

### BrowserManager

浏览器管理器，负责浏览器实例的创建和管理。

```python
from playwright_automation import BrowserManager, browser_manager

# 单例模式
mgr = BrowserManager()

# 启动
mgr.start()

# 启动浏览器
browser = mgr.launch_browser(
    browser_type="chromium",  # chromium, firefox, webkit
    headless=False,
    slow_mo=100  # 慢动作延迟
)

# 创建上下文
context = mgr.create_context(
    context_id="test",
    viewport={"width": 1920, "height": 1080},
    locale="zh-CN"
)

# 创建页面
page = mgr.new_page(context_id="test", page_id="home")

# 关闭
mgr.close_all()
mgr.stop()
```

### BasePage

页面操作基类，提供所有页面操作方法。

```python
from playwright_automation import BasePage

page = BasePage(page, url="https://example.com")

# 导航
page.goto(url="https://example.com")
page.back()
page.forward()
page.refresh()

# 元素操作
page.click("#button")
page.fill("#input", "text")
page.type_text("#input", "text", delay=50)
page.select_option("#dropdown", "value")
page.check("#checkbox")
page.hover("#menu-item")

# 等待
page.wait_for_selector("#element", timeout=10, state="visible")
page.wait_for_load_state("networkidle")

# 断言
page.is_visible("#element")
page.is_enabled("#button")
page.text_content("#title")

# 特殊操作
page.upload_file("#file-input", "path/to/file")
page.drag_and_drop("#source", "#target")
page.screenshot(path="screenshot.png")
```

### 配置

通过环境变量或 `.env` 文件配置：

```bash
# .env
TEST_ENV=dev
BASE_URL=https://example.com
BROWSER_TYPE=chromium
HEADLESS=false
TIMEOUT_DEFAULT=30000
LOG_LEVEL=INFO
SCREENSHOT_ON_FAILURE=true
```

## 🛠️ 最佳实践

### 1. 使用显式等待

```python
# ✅ 推荐
page.wait_for_selector("#element", timeout=10000)
page.click("#element")

# ❌ 避免
time.sleep(5)
page.click("#element")
```

### 2. 使用BasePage方法

```python
# ✅ 推荐
base_page = BasePage(page)
base_page.fill("#input", "text")
base_page.click("#button")

# ❌ 避免
page.fill("#input", "text")
page.click("#button")
```

### 3. 失败时自动截图

```python
try:
    page.click("#button")
except Exception as e:
    page.screenshot(path=f"error_{int(time.time())}.png")
    raise
```

### 4. 使用有意义的定位器

```python
# ✅ 推荐
page.click("[data-testid='submit-button']")
page.click("#main-form .submit-btn")

# ❌ 避免
page.click("body > div > div > div > button:nth-child(3)")
```

## 🧪 测试运行

### 本地运行

```bash
# 运行所有测试
pytest tests/

# 运行并显示输出
pytest tests/ -v -s

# 运行特定测试文件
pytest tests/test_example.py

# 运行带标记的测试
pytest -m smoke tests/
```

### 生成报告

```bash
# 使用pytest-html
pip install pytest-html
pytest tests/ --html=reports/report.html --self-contained-html

# 使用Allure
pip install allure-pytest
pytest tests/ --alluredir=reports/allure-results
allure serve reports/allure-results
```

### CI/CD 集成

```yaml
# GitHub Actions 示例
name: Playwright Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium
      - name: Run tests
        run: pytest tests/ -v
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 联系方式

- GitHub Issues: [提交问题](https://github.com/your-repo/issues)
- Email: support@example.com

---

<p align="center">
  <strong>Made with ❤️ by Playwright Automation Team</strong>
</p>
