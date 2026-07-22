"""
浏览器管理模块
负责浏览器实例的创建、配置和管理
"""
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Playwright
from playwright.sync_api._impl._helper import SSL_CERT_ERRORS

from config.settings import settings, BrowserConfig


class BrowserManager:
    """浏览器管理器 - 单例模式"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._contexts: Dict[str, BrowserContext] = {}
        self._pages: Dict[str, Page] = {}
        self._logger = logging.getLogger(self.__class__.__name__)
        
        self._initialized = True
    
    def start(self) -> 'BrowserManager':
        """启动Playwright"""
        if self._playwright is None:
            self._playwright = sync_playwright().start()
            self._logger.info("Playwright 已启动")
        return self
    
    def stop(self) -> 'BrowserManager':
        """停止Playwright"""
        self.close_all()
        
        if self._playwright:
            self._playwright.stop()
            self._playwright = None
            self._logger.info("Playwright 已停止")
        
        return self
    
    def launch_browser(self, config: Optional[BrowserConfig] = None) -> Browser:
        """启动浏览器"""
        if self._browser:
            self._logger.warning("浏览器已存在，直接返回")
            return self._browser
        
        config = config or settings.browser
        self.start()
        
        # 构建浏览器启动参数
        launch_options = {
            "headless": config.headless,
            "slow_mo": config.slow_mo,
        }
        
        if config.executable_path:
            launch_options["executable_path"] = config.executable_path
        
        if config.args:
            launch_options["args"] = config.args
        
        # 根据浏览器类型启动
        browser_type_map = {
            "chromium": self._playwright.chromium,
            "firefox": self._playwright.firefox,
            "webkit": self._playwright.webkit,
        }
        
        browser_launcher = browser_type_map.get(config.browser_type)
        if not browser_launcher:
            raise ValueError(f"不支持的浏览器类型: {config.browser_type}")
        
        self._browser = browser_launcher.launch(**launch_options)
        self._logger.info(f"{config.browser_type} 浏览器已启动 (headless={config.headless})")
        
        return self._browser
    
    def close_browser(self) -> 'BrowserManager':
        """关闭浏览器"""
        if self._browser:
            self._browser.close()
            self._browser = None
            self._logger.info("浏览器已关闭")
        
        return self
    
    def create_context(
        self,
        context_id: str = "default",
        **kwargs
    ) -> BrowserContext:
        """创建浏览器上下文"""
        if not self._browser:
            self.launch_browser()
        
        # 合并配置
        viewport = kwargs.pop("viewport", settings.browser.viewport)
        user_agent = kwargs.pop("user_agent", settings.browser.user_agent)
        locale = kwargs.pop("locale", "zh-CN")
        timezone_id = kwargs.pop("timezone_id", "Asia/Shanghai")
        
        context_options = {
            "viewport": viewport,
            "locale": locale,
            "timezone_id": timezone_id,
            "color_scheme": kwargs.pop("color_scheme", None),  # light, dark, null
            "device_scale_factor": kwargs.pop("device_scale_factor", settings.browser.device_scale_factor),
            "is_mobile": kwargs.pop("is_mobile", settings.browser.is_mobile),
            "has_touch": kwargs.pop("has_touch", settings.browser.has_touch),
        }
        
        if user_agent:
            context_options["user_agent"] = user_agent
        
        # 代理设置
        if settings.browser.proxy:
            context_options["proxy"] = settings.browser.proxy
        
        # 权限设置
        if settings.browser.permissions:
            context_options["permissions"] = settings.browser.permissions
        
        # 添加其他自定义参数
        context_options.update(kwargs)
        
        context = self._browser.new_context(**context_options)
        self._contexts[context_id] = context
        
        self._logger.info(f"浏览器上下文 '{context_id}' 已创建")
        
        return context
    
    def get_context(self, context_id: str = "default") -> Optional[BrowserContext]:
        """获取浏览器上下文"""
        return self._contexts.get(context_id)
    
    def close_context(self, context_id: str = "default") -> 'BrowserManager':
        """关闭浏览器上下文"""
        if context_id in self._contexts:
            self._contexts[context_id].close()
            del self._contexts[context_id]
            self._logger.info(f"浏览器上下文 '{context_id}' 已关闭")
        
        return self
    
    def new_page(
        self,
        context_id: str = "default",
        page_id: Optional[str] = None,
        **kwargs
    ) -> Page:
        """创建新页面"""
        context = self.get_context(context_id)
        if not context:
            context = self.create_context(context_id)
        
        page = context.new_page(**kwargs)
        page_id = page_id or f"page_{len(self._pages) + 1}"
        self._pages[page_id] = page
        
        # 设置默认超时
        page.set_default_timeout(settings.timeouts.default)
        
        self._logger.info(f"页面 '{page_id}' 已创建")
        
        return page
    
    def get_page(self, page_id: str) -> Optional[Page]:
        """获取页面"""
        return self._pages.get(page_id)
    
    def close_page(self, page_id: str) -> 'BrowserManager':
        """关闭页面"""
        if page_id in self._pages:
            self._pages[page_id].close()
            del self._pages[page_id]
            self._logger.info(f"页面 '{page_id}' 已关闭")
        
        return self
    
    def close_all(self) -> 'BrowserManager':
        """关闭所有页面和上下文"""
        # 关闭所有页面
        for page_id in list(self._pages.keys()):
            self.close_page(page_id)
        
        # 关闭所有上下文
        for context_id in list(self._contexts.keys()):
            self.close_context(context_id)
        
        # 关闭浏览器
        self.close_browser()
        
        return self
    
    @contextmanager
    def page_context(self, context_id: str = "default", page_id: Optional[str] = None):
        """页面上下文管理器"""
        page = self.new_page(context_id, page_id)
        try:
            yield page
        finally:
            if page_id:
                self.close_page(page_id)
    
    def set_auth_state(self, context_id: str, storage_state: Dict) -> 'BrowserManager':
        """设置认证状态（cookies, localStorage等）"""
        context = self.get_context(context_id)
        if context:
            context.add_cookies(storage_state.get("cookies", []))
        return self
    
    def get_auth_state(self, context_id: str = "default") -> Dict:
        """获取认证状态"""
        context = self.get_context(context_id)
        if context:
            return context.storage_state()
        return {}
    
    def take_screenshot(
        self,
        page_id: str = None,
        path: Optional[str] = None,
        full_page: bool = False,
        **kwargs
    ) -> bytes:
        """截图"""
        page = self.get_page(page_id) if page_id else self.get_current_page()
        if not page:
            raise ValueError("没有可用的页面进行截图")
        
        path = path or f"screenshots/screenshot_{int(time.time())}.png"
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        return page.screenshot(path=path, full_page=full_page, **kwargs)
    
    def get_current_page(self) -> Optional[Page]:
        """获取当前活动页面"""
        if self._pages:
            return list(self._pages.values())[-1]
        return None
    
    @property
    def browser(self) -> Optional[Browser]:
        return self._browser
    
    @property
    def is_running(self) -> bool:
        return self._playwright is not None


# 全局浏览器管理器实例
browser_manager = BrowserManager()
