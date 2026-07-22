"""
页面基类模块
提供页面操作的基础封装
"""
import time
import logging
from typing import Optional, Union, List, Dict, Any, Callable
from pathlib import Path

from playwright.sync_api import Page, Locator, TimeoutError as PlaywrightTimeout
from playwright.sync_api._impl._helper import expect

from config.settings import settings
from config.locators import Locator as CustomLocator


class BasePage:
    """页面操作基类"""
    
    # 默认超时时间
    DEFAULT_TIMEOUT = settings.timeouts.default / 1000  # 转换为秒
    DEFAULT_INTERVAL = 0.5  # 轮询间隔
    
    def __init__(self, page: Page, url: Optional[str] = None):
        self._page = page
        self._url = url
        self._logger = logging.getLogger(f"{self.__class__.__name__}")
        self._loaded = False
    
    @property
    def page(self) -> Page:
        """获取Playwright页面对象"""
        return self._page
    
    @property
    def url(self) -> str:
        """获取当前页面URL"""
        return self._page.url
    
    @property
    def title(self) -> str:
        """获取页面标题"""
        return self._page.title()
    
    def goto(
        self,
        url: Optional[str] = None,
        wait_until: str = "load",
        timeout: Optional[float] = None
    ) -> 'BasePage':
        """导航到指定URL"""
        url = url or self._url
        if not url:
            raise ValueError("URL is required")
        
        timeout = timeout or (settings.timeouts.navigation / 1000)
        
        self._logger.info(f"导航到: {url}")
        self._page.goto(url, wait_until=wait_until, timeout=timeout * 1000)
        self._loaded = True
        
        return self
    
    def back(self) -> 'BasePage':
        """返回上一页"""
        self._page.go_back()
        return self
    
    def forward(self) -> 'BasePage':
        """前进到下一页"""
        self._page.go_forward()
        return self
    
    def refresh(self) -> 'BasePage':
        """刷新页面"""
        self._page.reload()
        return self
    
    def wait_for_load_state(
        self,
        state: str = "load",
        timeout: Optional[float] = None
    ) -> 'BasePage':
        """等待页面加载状态"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        self._page.wait_for_load_state(state, timeout=timeout * 1000)
        return self
    
    def wait_for_url(self, url: str, timeout: Optional[float] = None) -> 'BasePage':
        """等待URL匹配"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        self._page.wait_for_url(url, timeout=timeout * 1000)
        return self
    
    def wait_for_function(self, func: str, timeout: Optional[float] = None, *args) -> 'BasePage':
        """等待JavaScript函数返回true"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        self._page.wait_for_function(func, timeout=timeout * 1000, *args)
        return self
    
    # ========== 元素定位和操作 ==========
    
    def locator(
        self,
        selector: str,
        has: Optional[str] = None,
        has_text: Optional[str] = None
    ) -> Locator:
        """获取元素定位器"""
        loc = self._page.locator(selector)
        if has:
            loc = loc.filter(has=has)
        if has_text:
            loc = loc.filter(has_text=has_text)
        return loc
    
    def get_element(
        self,
        selector: str,
        timeout: Optional[float] = None,
        state: str = "visible"
    ) -> Locator:
        """获取单个元素"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        loc = self.locator(selector)
        loc.wait_for(timeout=timeout * 1000, state=state)
        return loc
    
    def get_elements(self, selector: str) -> List[Locator]:
        """获取元素列表"""
        return self.locator(selector).all()
    
    def click(
        self,
        selector: str,
        timeout: Optional[float] = None,
        button: str = "left",
        click_count: int = 1,
        modifiers: Optional[List[str]] = None,
        position: Optional[Dict[str, int]] = None,
        force: bool = False
    ) -> 'BasePage':
        """点击元素"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        loc = self.get_element(selector, timeout)
        loc.click(
            timeout=timeout * 1000,
            button=button,
            click_count=click_count,
            modifiers=modifiers,
            position=position,
            force=force
        )
        self._logger.info(f"点击元素: {selector}")
        return self
    
    def dblclick(
        self,
        selector: str,
        timeout: Optional[float] = None,
        button: str = "left",
        modifiers: Optional[List[str]] = None,
        position: Optional[Dict[str, int]] = None
    ) -> 'BasePage':
        """双击元素"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        loc = self.get_element(selector, timeout)
        loc.dblclick(
            timeout=timeout * 1000,
            button=button,
            modifiers=modifiers,
            position=position
        )
        self._logger.info(f"双击元素: {selector}")
        return self
    
    def right_click(self, selector: str, timeout: Optional[float] = None) -> 'BasePage':
        """右键点击"""
        return self.click(selector, timeout=timeout, button="right")
    
    def hover(self, selector: str, timeout: Optional[float] = None) -> 'BasePage':
        """悬停到元素"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        loc = self.get_element(selector, timeout)
        loc.hover(timeout=timeout * 1000)
        return self
    
    # ========== 输入操作 ==========
    
    def fill(self, selector: str, value: str, timeout: Optional[float] = None) -> 'BasePage':
        """填充输入框（清空后输入）"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        loc = self.get_element(selector, timeout)
        loc.fill(value)
        self._logger.info(f"填充字段: {selector} = {value}")
        return self
    
    def type_text(
        self,
        selector: str,
        text: str,
        delay: float = 0,
        timeout: Optional[float] = None
    ) -> 'BasePage':
        """逐字输入文本"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        loc = self.get_element(selector, timeout)
        loc.type(text, delay=delay)
        self._logger.info(f"输入文本: {selector} = {text}")
        return self
    
    def input_value(self, selector: str) -> str:
        """获取输入框的值"""
        loc = self.locator(selector)
        return loc.input_value()
    
    def clear(self, selector: str, timeout: Optional[float] = None) -> 'BasePage':
        """清空输入框"""
        return self.fill(selector, "", timeout)
    
    def press(self, selector: str, key: str, timeout: Optional[float] = None) -> 'BasePage':
        """按键盘键"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        loc = self.get_element(selector, timeout)
        loc.press(key)
        return self
    
    # ========== 选择操作 ==========
    
    def select_option(
        self,
        selector: str,
        value: Union[str, List[str]],
        timeout: Optional[float] = None
    ) -> 'BasePage':
        """选择下拉选项"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        loc = self.get_element(selector, timeout)
        loc.select_option(value)
        return self
    
    def check(self, selector: str, timeout: Optional[float] = None) -> 'BasePage':
        """勾选复选框"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        loc = self.get_element(selector, timeout)
        loc.check()
        return self
    
    def uncheck(self, selector: str, timeout: Optional[float] = None) -> 'BasePage':
        """取消勾选复选框"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        loc = self.get_element(selector, timeout)
        loc.uncheck()
        return self
    
    def is_checked(self, selector: str) -> bool:
        """检查是否选中"""
        return self.locator(selector).is_checked()
    
    # ========== 等待和断言 ==========
    
    def wait_for_selector(
        self,
        selector: str,
        timeout: Optional[float] = None,
        state: str = "visible"
    ) -> Locator:
        """等待元素出现"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        loc = self.locator(selector)
        loc.wait_for(timeout=timeout * 1000, state=state)
        return loc
    
    def wait_for_selector_hidden(
        self,
        selector: str,
        timeout: Optional[float] = None
    ) -> 'BasePage':
        """等待元素消失"""
        self.wait_for_selector(selector, timeout, state="hidden")
        return self
    
    def wait_for_element_count(
        self,
        selector: str,
        count: int,
        timeout: Optional[float] = None
    ) -> 'BasePage':
        """等待元素数量达到预期"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        end_time = time.time() + timeout
        
        while time.time() < end_time:
            elements = self.locator(selector).all()
            if len(elements) >= count:
                return self
            time.sleep(self.DEFAULT_INTERVAL)
        
        raise TimeoutError(f"等待 {count} 个元素 '{selector}' 失败")
    
    def is_visible(self, selector: str) -> bool:
        """检查元素是否可见"""
        return self.locator(selector).is_visible()
    
    def is_hidden(self, selector: str) -> bool:
        """检查元素是否隐藏"""
        return self.locator(selector).is_hidden()
    
    def is_enabled(self, selector: str) -> bool:
        """检查元素是否可用"""
        return self.locator(selector).is_enabled()
    
    def is_disabled(self, selector: str) -> bool:
        """检查元素是否禁用"""
        return not self.is_enabled(selector)
    
    def text_content(self, selector: str) -> str:
        """获取文本内容"""
        return self.locator(selector).text_content()
    
    def inner_html(self, selector: str) -> str:
        """获取HTML内容"""
        return self.locator(selector).inner_html()
    
    def inner_text(self, selector: str) -> str:
        """获取内部文本"""
        return self.locator(selector).inner_text()
    
    def get_attribute(self, selector: str, name: str) -> str:
        """获取元素属性"""
        return self.locator(selector).get_attribute(name)
    
    # ========== 滚动操作 ==========
    
    def scroll_to_element(self, selector: str, timeout: Optional[float] = None) -> 'BasePage':
        """滚动到元素位置"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        loc = self.get_element(selector, timeout)
        loc.scroll_into_view_if_needed()
        return self
    
    def scroll_by_amount(self, x: int, y: int) -> 'BasePage':
        """滚动指定距离"""
        self._page.mouse.wheel(x, y)
        return self
    
    def scroll_to_top(self) -> 'BasePage':
        """滚动到顶部"""
        self._page.evaluate("window.scrollTo(0, 0)")
        return self
    
    def scroll_to_bottom(self) -> 'BasePage':
        """滚动到底部"""
        self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        return self
    
    # ========== 特殊操作 ==========
    
    def drag_and_drop(
        self,
        source: str,
        target: str,
        timeout: Optional[float] = None
    ) -> 'BasePage':
        """拖拽操作"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        source_loc = self.get_element(source, timeout)
        target_loc = self.get_element(target, timeout)
        source_loc.drag_to(target_loc)
        self._logger.info(f"拖拽: {source} -> {target}")
        return self
    
    def upload_file(
        self,
        selector: str,
        file_path: Union[str, List[str]],
        timeout: Optional[float] = None
    ) -> 'BasePage':
        """文件上传"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        loc = self.get_element(selector, timeout)
        loc.set_input_files(file_path)
        return self
    
    def evaluate(self, expression: str, *args):
        """执行JavaScript"""
        return self._page.evaluate(expression, *args)
    
    def evaluate_on_selector(self, selector: str, expression: str, *args):
        """在元素上执行JavaScript"""
        return self.locator(selector).evaluate(expression, *args)
    
    # ========== 截图和录制 ==========
    
    def screenshot(
        self,
        path: Optional[str] = None,
        full_page: bool = False,
        **kwargs
    ) -> bytes:
        """页面截图"""
        path = path or f"screenshots/screenshot_{int(time.time())}.png"
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        return self._page.screenshot(path=path, full_page=full_page, **kwargs)
    
    def element_screenshot(
        self,
        selector: str,
        path: Optional[str] = None,
        **kwargs
    ) -> bytes:
        """元素截图"""
        path = path or f"screenshots/element_{int(time.time())}.png"
        loc = self.locator(selector)
        return loc.screenshot(path=path, **kwargs)
    
    # ========== Frame操作 ==========
    
    def frame(self, selector: str) -> 'BasePage':
        """切换到iframe"""
        frame = self._page.frame(selector=selector)
        return BasePage(frame) if frame else None
    
    def main_frame(self) -> 'BasePage':
        """切换回主框架"""
        return BasePage(self._page.main_frame)
    
    # ========== 对话框处理 ==========
    
    def on_dialog(self, handler: Callable) -> 'BasePage':
        """监听对话框"""
        self._page.on("dialog", handler)
        return self
    
    def accept_dialog(self, prompt_text: Optional[str] = None) -> 'BasePage':
        """接受对话框"""
        self._page.on("dialog", lambda dialog: dialog.accept(prompt_text))
        return self
    
    def dismiss_dialog(self) -> 'BasePage':
        """关闭对话框"""
        self._page.on("dialog", lambda dialog: dialog.dismiss())
        return self
    
    def __repr__(self):
        return f"<{self.__class__.__name__} url={self.url}>"


class PageManager:
    """页面管理器 - 管理多个页面实例"""
    
    def __init__(self):
        self._pages: Dict[str, BasePage] = {}
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def register(self, name: str, page: BasePage) -> None:
        """注册页面"""
        self._pages[name] = page
        self._logger.info(f"页面已注册: {name}")
    
    def get(self, name: str) -> Optional[BasePage]:
        """获取页面"""
        return self._pages.get(name)
    
    def unregister(self, name: str) -> None:
        """注销页面"""
        if name in self._pages:
            del self._pages[name]
    
    def get_all(self) -> Dict[str, BasePage]:
        """获取所有页面"""
        return self._pages.copy()
    
    def clear(self) -> None:
        """清空所有页面"""
        self._pages.clear()
