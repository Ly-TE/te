"""
元素操作处理模块
提供更高级的元素操作封装
"""
import time
import logging
from typing import Optional, Union, List, Dict, Any, Callable
from playwright.sync_api import Locator, Page

from config.settings import settings


class ElementHandler:
    """元素操作处理器"""
    
    DEFAULT_TIMEOUT = settings.timeouts.default / 1000
    RETRY_INTERVAL = 0.5
    
    def __init__(self, page: Page):
        self._page = page
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def retry_click(
        self,
        selector: str,
        max_retries: int = 3,
        timeout: Optional[float] = None,
        expected_condition: Optional[Callable] = None
    ) -> bool:
        """
        重试点击操作
        
        Args:
            selector: 元素选择器
            max_retries: 最大重试次数
            timeout: 超时时间
            expected_condition: 期望条件函数
        """
        timeout = timeout or self.DEFAULT_TIMEOUT
        end_time = time.time() + timeout
        
        for attempt in range(max_retries):
            try:
                loc = self._page.locator(selector)
                loc.wait_for(timeout=2000, state="visible")
                loc.click(timeout=3000)
                
                # 如果有期望条件，验证条件
                if expected_condition and not expected_condition():
                    raise AssertionError("期望条件未满足")
                
                self._logger.info(f"点击成功 (尝试 {attempt + 1}/{max_retries}): {selector}")
                return True
                
            except Exception as e:
                self._logger.warning(f"点击失败 (尝试 {attempt + 1}/{max_retries}): {selector}, 错误: {e}")
                
                if time.time() >= end_time:
                    raise
                
                time.sleep(self.RETRY_INTERVAL)
        
        raise TimeoutError(f"点击失败，已重试 {max_retries} 次: {selector}")
    
    def smart_wait(
        self,
        selector: str,
        state: str = "visible",
        timeout: Optional[float] = None
    ) -> bool:
        """
        智能等待元素状态
        
        Args:
            selector: 元素选择器
            state: 状态 (visible, hidden, attached, detached)
            timeout: 超时时间
        """
        timeout = timeout or self.DEFAULT_TIMEOUT
        
        try:
            loc = self._page.locator(selector)
            loc.wait_for(timeout=timeout * 1000, state=state)
            return True
        except Exception as e:
            self._logger.warning(f"等待元素状态 '{state}' 失败: {selector}")
            return False
    
    def wait_for_text(
        self,
        selector: str,
        text: str,
        timeout: Optional[float] = None
    ) -> bool:
        """等待元素包含特定文本"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        end_time = time.time() + timeout
        
        while time.time() < end_time:
            try:
                loc = self._page.locator(selector)
                if text in (loc.text_content() or ""):
                    return True
            except:
                pass
            time.sleep(self.RETRY_INTERVAL)
        
        return False
    
    def wait_for_value(
        self,
        selector: str,
        value: str,
        timeout: Optional[float] = None
    ) -> bool:
        """等待输入框值匹配"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        end_time = time.time() + timeout
        
        while time.time() < end_time:
            try:
                loc = self._page.locator(selector)
                if loc.input_value() == value:
                    return True
            except:
                pass
            time.sleep(self.RETRY_INTERVAL)
        
        return False
    
    def wait_for_load(
        self,
        timeout: Optional[float] = None,
        wait_for_network: bool = True
    ) -> 'ElementHandler':
        """等待页面加载完成"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        
        self._page.wait_for_load_state("domcontentloaded", timeout=timeout * 1000)
        
        if wait_for_network:
            try:
                self._page.wait_for_load_state("networkidle", timeout=timeout * 1000)
            except:
                self._logger.warning("等待网络空闲超时，继续执行")
        
        return self
    
    def wait_for_ajax(
        self,
        timeout: Optional[float] = None
    ) -> 'ElementHandler':
        """等待所有AJAX请求完成"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        
        self._page.wait_for_function("""
            () => {
                return window.jQuery ? jQuery.active === 0 : true;
            }
        """, timeout=timeout * 1000)
        
        return self
    
    def scroll_and_click(
        self,
        selector: str,
        timeout: Optional[float] = None
    ) -> bool:
        """滚动到元素位置并点击"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        
        try:
            loc = self._page.locator(selector)
            loc.scroll_into_view_if_needed()
            time.sleep(0.3)  # 等待滚动完成
            loc.click(timeout=timeout * 1000)
            return True
        except Exception as e:
            self._logger.error(f"滚动点击失败: {selector}, 错误: {e}")
            return False
    
    def force_click(
        self,
        selector: str,
        timeout: Optional[float] = None
    ) -> bool:
        """强制点击（即使元素不可见或被遮挡）"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        
        try:
            loc = self._page.locator(selector)
            loc.click(timeout=timeout * 1000, force=True)
            return True
        except Exception as e:
            self._logger.error(f"强制点击失败: {selector}, 错误: {e}")
            return False
    
    def hover_and_click(
        self,
        hover_selector: str,
        click_selector: str,
        timeout: Optional[float] = None
    ) -> bool:
        """悬停后点击"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        
        try:
            # 悬停到第一个元素
            hover_loc = self._page.locator(hover_selector)
            hover_loc.hover(timeout=timeout * 1000)
            time.sleep(0.3)
            
            # 点击第二个元素
            click_loc = self._page.locator(click_selector)
            click_loc.click(timeout=timeout * 1000)
            return True
        except Exception as e:
            self._logger.error(f"悬停点击失败: {hover_selector} -> {click_selector}, 错误: {e}")
            return False
    
    def get_table_data(
        self,
        table_selector: str,
        header: bool = True
    ) -> List[Dict[str, str]]:
        """获取表格数据"""
        data = []
        
        try:
            table = self._page.locator(table_selector)
            
            # 获取表头
            headers = []
            if header:
                header_cells = table.locator("thead th").all()
                headers = [cell.text_content() for cell in header_cells]
            
            # 获取表格行
            rows = table.locator("tbody tr").all()
            
            for row in rows:
                cells = row.locator("td").all()
                if header and headers:
                    row_data = {headers[i]: cells[i].text_content() for i in range(len(cells))}
                else:
                    row_data = [cell.text_content() for cell in cells]
                data.append(row_data)
            
        except Exception as e:
            self._logger.error(f"获取表格数据失败: {table_selector}, 错误: {e}")
        
        return data
    
    def get_list_items(
        self,
        list_selector: str,
        item_selector: str = "li"
    ) -> List[str]:
        """获取列表项文本"""
        items = []
        
        try:
            loc = self._page.locator(list_selector)
            list_items = loc.locator(item_selector).all()
            items = [item.text_content() for item in list_items]
        except Exception as e:
            self._logger.error(f"获取列表项失败: {list_selector}, 错误: {e}")
        
        return items
    
    def find_element_by_text(
        self,
        text: str,
        selector: str = "*"
    ) -> Optional[Locator]:
        """通过文本查找元素"""
        try:
            return self._page.locator(selector, has_text=text).first
        except:
            return None
    
    def find_elements_by_text(
        self,
        text: str,
        selector: str = "*"
    ) -> List[Locator]:
        """通过文本查找所有匹配元素"""
        try:
            return self._page.locator(selector, has_text=text).all()
        except:
            return []
    
    def execute_script(
        self,
        script: str,
        *args
    ) -> Any:
        """执行JavaScript脚本"""
        return self._page.evaluate(script, *args)
    
    def highlight_element(
        self,
        selector: str,
        duration: float = 1.0
    ) -> 'ElementHandler':
        """高亮显示元素（用于调试）"""
        try:
            self._page.evaluate("""
                (selector) => {
                    const el = document.querySelector(selector);
                    if (el) {
                        const original = el.style.border;
                        el.style.border = '3px solid red';
                        setTimeout(() => el.style.border = original, arguments[0]);
                    }
                }
            """, selector, duration * 1000)
        except Exception as e:
            self._logger.error(f"高亮元素失败: {selector}, 错误: {e}")
        
        return self
    
    def is_element_exists(self, selector: str) -> bool:
        """检查元素是否存在"""
        return self._page.locator(selector).count() > 0
    
    def get_element_count(self, selector: str) -> int:
        """获取匹配元素数量"""
        return self._page.locator(selector).count()
    
    def get_all_text(
        self,
        selector: str,
        separator: str = "\n"
    ) -> str:
        """获取所有匹配元素的文本"""
        try:
            elements = self._page.locator(selector).all()
            return separator.join([el.text_content() for el in elements])
        except:
            return ""
