"""
断言辅助模块
提供丰富的断言方法和工具
"""
import re
import time
import logging
from typing import Any, Optional, Union, List, Dict, Callable
from playwright.sync_api import Page, Locator


class AssertionError(Exception):
    """断言错误"""
    pass


class AssertHelper:
    """断言辅助类"""
    
    @staticmethod
    def assert_true(condition: bool, message: str = "断言失败"):
        """断言为True"""
        if not condition:
            raise AssertionError(message)
    
    @staticmethod
    def assert_false(condition: bool, message: str = "断言失败"):
        """断言为False"""
        if condition:
            raise AssertionError(message)
    
    @staticmethod
    def assert_equal(actual: Any, expected: Any, message: str = ""):
        """断言相等"""
        if actual != expected:
            msg = message or f"期望 {expected}，实际 {actual}"
            raise AssertionError(msg)
    
    @staticmethod
    def assert_not_equal(actual: Any, expected: Any, message: str = ""):
        """断言不相等"""
        if actual == expected:
            msg = message or f"期望不等于 {expected}，实际 {actual}"
            raise AssertionError(msg)
    
    @staticmethod
    def assert_none(value: Any, message: str = "期望 None"):
        """断言为None"""
        if value is not None:
            raise AssertionError(f"{message}，实际 {value}")
    
    @staticmethod
    def assert_not_none(value: Any, message: str = "期望不为 None"):
        """断言不为None"""
        if value is None:
            raise AssertionError(message)
    
    @staticmethod
    def assert_in(actual: Any, expected: Union[List, str, Dict], message: str = ""):
        """断言包含"""
        if actual not in expected:
            msg = message or f"期望 {actual} 在 {expected} 中"
            raise AssertionError(msg)
    
    @staticmethod
    def assert_not_in(actual: Any, expected: Union[List, str], message: str = ""):
        """断言不包含"""
        if actual in expected:
            msg = message or f"期望 {actual} 不在 {expected} 中"
            raise AssertionError(msg)
    
    @staticmethod
    def assert_greater(actual: Any, expected: Any, message: str = ""):
        """断言大于"""
        if not actual > expected:
            msg = message or f"期望 {actual} > {expected}"
            raise AssertionError(msg)
    
    @staticmethod
    def assert_less(actual: Any, expected: Any, message: str = ""):
        """断言小于"""
        if not actual < expected:
            msg = message or f"期望 {actual} < {expected}"
            raise AssertionError(msg)
    
    @staticmethod
    def assert_contains(actual: str, expected: str, message: str = ""):
        """断言字符串包含"""
        if expected not in actual:
            msg = message or f"期望字符串 '{actual}' 包含 '{expected}'"
            raise AssertionError(msg)
    
    @staticmethod
    def assert_matches(text: str, pattern: str, message: str = ""):
        """断言正则匹配"""
        if not re.search(pattern, text):
            msg = message or f"文本 '{text}' 不匹配模式 '{pattern}'"
            raise AssertionError(msg)
    
    @staticmethod
    def assert_starts_with(text: str, prefix: str, message: str = ""):
        """断言字符串开头"""
        if not text.startswith(prefix):
            msg = message or f"期望 '{text}' 以 '{prefix}' 开头"
            raise AssertionError(msg)
    
    @staticmethod
    def assert_ends_with(text: str, suffix: str, message: str = ""):
        """断言字符串结尾"""
        if not text.endswith(suffix):
            msg = message or f"期望 '{text}' 以 '{suffix}' 结尾"
            raise AssertionError(msg)
    
    @staticmethod
    def assert_length(arr: List, length: int, message: str = ""):
        """断言列表长度"""
        if len(arr) != length:
            msg = message or f"期望长度 {length}，实际 {len(arr)}"
            raise AssertionError(msg)
    
    @staticmethod
    def assert_list_not_empty(arr: List, message: str = "期望列表非空"):
        """断言列表非空"""
        if len(arr) == 0:
            raise AssertionError(message)
    
    @staticmethod
    def assert_dict_keys(data: Dict, keys: List[str], message: str = ""):
        """断言字典包含指定键"""
        missing = set(keys) - set(data.keys())
        if missing:
            msg = message or f"字典缺少键: {missing}"
            raise AssertionError(msg)
    
    @staticmethod
    def assert_type(value: Any, expected_type: type, message: str = ""):
        """断言类型"""
        if not isinstance(value, expected_type):
            msg = message or f"期望类型 {expected_type}，实际 {type(value)}"
            raise AssertionError(msg)


class Assertions:
    """页面断言类"""
    
    def __init__(self, page: Page):
        self._page = page
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def url_contains(self, text: str, message: str = ""):
        """断言URL包含文本"""
        actual = self._page.url
        AssertHelper.assert_contains(actual, text, message)
    
    def url_matches(self, pattern: str, message: str = ""):
        """断言URL匹配正则"""
        actual = self._page.url
        AssertHelper.assert_matches(actual, pattern, message)
    
    def title_contains(self, text: str, message: str = ""):
        """断言标题包含文本"""
        actual = self._page.title()
        AssertHelper.assert_contains(actual, text, message)
    
    def title_matches(self, pattern: str, message: str = ""):
        """断言标题匹配正则"""
        actual = self._page.title()
        AssertHelper.assert_matches(actual, pattern, message)
    
    def element_visible(self, selector: str, message: str = ""):
        """断言元素可见"""
        loc = self._page.locator(selector)
        if not loc.is_visible():
            msg = message or f"元素不可见: {selector}"
            raise AssertionError(msg)
    
    def element_hidden(self, selector: str, message: str = ""):
        """断言元素隐藏"""
        loc = self._page.locator(selector)
        if not loc.is_hidden():
            msg = message or f"元素可见: {selector}"
            raise AssertionError(msg)
    
    def element_exists(self, selector: str, message: str = ""):
        """断言元素存在"""
        count = self._page.locator(selector).count()
        if count == 0:
            msg = message or f"元素不存在: {selector}"
            raise AssertionError(msg)
    
    def element_count(self, selector: str, count: int, message: str = ""):
        """断言元素数量"""
        actual = self._page.locator(selector).count()
        AssertHelper.assert_equal(actual, count, message)
    
    def element_text_contains(self, selector: str, text: str, message: str = ""):
        """断言元素文本包含"""
        actual = self._page.locator(selector).text_content()
        AssertHelper.assert_contains(actual, text, message)
    
    def element_text_equals(self, selector: str, text: str, message: str = ""):
        """断言元素文本相等"""
        actual = self._page.locator(selector).text_content()
        AssertHelper.assert_equal(actual, text, message)
    
    def element_value(self, selector: str, value: str, message: str = ""):
        """断言输入框值"""
        actual = self._page.locator(selector).input_value()
        AssertHelper.assert_equal(actual, value, message)
    
    def element_enabled(self, selector: str, message: str = ""):
        """断言元素可用"""
        loc = self._page.locator(selector)
        if not loc.is_enabled():
            msg = message or f"元素不可用: {selector}"
            raise AssertionError(msg)
    
    def element_disabled(self, selector: str, message: str = ""):
        """断言元素禁用"""
        loc = self._page.locator(selector)
        if loc.is_enabled():
            msg = message or f"元素可用: {selector}"
            raise AssertionError(msg)
    
    def element_checked(self, selector: str, message: str = ""):
        """断言复选框/单选框选中"""
        loc = self._page.locator(selector)
        if not loc.is_checked():
            msg = message or f"元素未选中: {selector}"
            raise AssertionError(msg)
    
    def element_unchecked(self, selector: str, message: str = ""):
        """断言复选框/单选框未选中"""
        loc = self._page.locator(selector)
        if loc.is_checked():
            msg = message or f"元素已选中: {selector}"
            raise AssertionError(msg)
    
    def attribute_contains(self, selector: str, attr: str, value: str, message: str = ""):
        """断言元素属性包含值"""
        actual = self._page.locator(selector).get_attribute(attr) or ""
        AssertHelper.assert_contains(actual, value, message)
    
    def attribute_equals(self, selector: str, attr: str, value: str, message: str = ""):
        """断言元素属性等于值"""
        actual = self._page.locator(selector).get_attribute(attr)
        AssertHelper.assert_equal(actual, value, message)
    
    def alert_present(self, message: str = "期望存在alert对话框"):
        """断言alert对话框存在"""
        # 捕获alert对话框
        alert_info = {"present": False}
        
        def handler(dialog):
            alert_info["present"] = True
            alert_info["message"] = dialog.message
            # 自动接受对话框
            dialog.accept()
        
        self._page.on("dialog", handler)
        
        if not alert_info["present"]:
            raise AssertionError(message)
    
    def page_contains_text(self, text: str, message: str = ""):
        """断言页面包含文本"""
        # 使用locator查找包含文本的元素
        loc = self._page.locator(f"text={text}")
        count = loc.count()
        if count == 0:
            msg = message or f"页面不包含文本: {text}"
            raise AssertionError(msg)
    
    def page_not_contains_text(self, text: str, message: str = ""):
        """断言页面不包含文本"""
        loc = self._page.locator(f"text={text}")
        count = loc.count()
        if count > 0:
            msg = message or f"页面包含文本: {text}"
            raise AssertionError(msg)


class WaitFor:
    """等待条件断言"""
    
    def __init__(self, page: Page):
        self._page = page
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def element(
        self,
        selector: str,
        timeout: float = 10,
        state: str = "visible"
    ) -> Locator:
        """等待元素"""
        loc = self._page.locator(selector)
        loc.wait_for(timeout=timeout * 1000, state=state)
        return loc
    
    def url(self, url: str, timeout: float = 10):
        """等待URL"""
        self._page.wait_for_url(url, timeout=timeout * 1000)
    
    def load_state(self, state: str = "load", timeout: float = 30):
        """等待加载状态"""
        self._page.wait_for_load_state(state, timeout=timeout * 1000)
    
    def function(self, func: str, timeout: float = 10, *args):
        """等待函数返回true"""
        self._page.wait_for_function(func, timeout=timeout * 1000, *args)
    
    def response(self, url: str, timeout: float = 10):
        """等待响应"""
        self._page.wait_for_response(lambda r: url in r.url, timeout=timeout * 1000)
    
    def navigation(self, timeout: float = 30):
        """等待导航完成"""
        self._page.wait_for_load_state("load", timeout=timeout * 1000)
