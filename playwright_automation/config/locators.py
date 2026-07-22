"""
页面元素定位器管理模块
支持集中管理页面元素的定位策略
"""
from typing import Dict, Union, List
from dataclasses import dataclass, field


@dataclass
class Locator:
    """元素定位器"""
    selector: str
    by: str = "css"  # css, xpath, text, id, name, class, role
    description: str = ""
    timeout: int = 0  # 0表示使用默认超时
    retries: int = 1  # 重试次数
    
    def __post_init__(self):
        # 自动生成描述
        if not self.description:
            self.description = f"{self.by}: {self.selector}"
    
    def to_playwright_locator(self, page):
        """转换为Playwright定位器"""
        by_mapping = {
            "css": "locator",
            "xpath": "locator",
            "text": "get_by_text",
            "id": "locator",
            "name": "locator",
            "class": "locator",
            "role": "get_by_role",
        }
        
        if self.by == "css" or self.by == "id" or self.by == "name" or self.by == "class":
            return page.locator(self.selector)
        elif self.by == "xpath":
            return page.locator(f"xpath={self.selector}")
        elif self.by == "text":
            return page.get_by_text(self.selector)
        elif self.by == "role":
            role, name = self.selector.split(":", 1) if ":" in self.selector else (self.selector, "")
            if name:
                return page.get_by_role(role.strip(), name=name.strip())
            return page.get_by_role(role.strip())
        else:
            return page.locator(self.selector)


class Locators:
    """页面元素定位器集合"""
    
    # ========== 通用定位器 ==========
    COMMON = {
        "button_primary": Locator("button.primary", "css", "主要按钮"),
        "button_secondary": Locator("button.secondary", "css", "次要按钮"),
        "input_text": Locator("input[type='text']", "css", "文本输入框"),
        "input_password": Locator("input[type='password']", "css", "密码输入框"),
        "input_email": Locator("input[type='email']", "css", "邮箱输入框"),
        "input_search": Locator("input[type='search']", "css", "搜索输入框"),
        "checkbox": Locator("input[type='checkbox']", "css", "复选框"),
        "radio": Locator("input[type='radio']", "css", "单选框"),
        "select": Locator("select", "css", "下拉选择框"),
        "link": Locator("a", "css", "链接"),
        "image": Locator("img", "css", "图片"),
        "table": Locator("table", "css", "表格"),
        "modal": Locator("[role='dialog']", "css", "模态框"),
        "alert": Locator("[role='alert']", "css", "警告框"),
    }
    
    # ========== Google搜索页面定位器 ==========
    GOOGLE_SEARCH = {
        "search_box": Locator("[name='q']", "css", "搜索框"),
        "search_button": Locator("[name='btnK']", "css", "搜索按钮"),
        "search_results": Locator("#search .g", "css", "搜索结果列表"),
        "result_link": Locator("#search a", "css", "结果链接"),
        "result_title": Locator("#search h3", "css", "结果标题"),
        "next_button": Locator("#pnnext", "css", "下一页按钮"),
        "lucky_button": Locator("[name='btnI']", "css", "手气不错按钮"),
        "logo": Locator("#hplogo", "css", "Google Logo"),
        "settings_button": Locator("[aria-label='Settings']", "css", "设置按钮"),
    }
    
    # ========== 登录页面定位器 ==========
    LOGIN = {
        "username_input": Locator("input[name='username']", "css", "用户名输入框"),
        "password_input": Locator("input[name='password']", "css", "密码输入框"),
        "login_button": Locator("button[type='submit']", "css", "登录按钮"),
        "remember_me": Locator("input[name='remember']", "css", "记住我"),
        "forgot_password": Locator("a.forgot-password", "css", "忘记密码链接"),
        "error_message": Locator(".error-message", "css", "错误消息"),
        "captcha": Locator("#captcha", "css", "验证码"),
    }
    
    # ========== 表单相关定位器 ==========
    FORM = {
        "submit_button": Locator("button[type='submit']", "css", "提交按钮"),
        "cancel_button": Locator("button.cancel", "css", "取消按钮"),
        "reset_button": Locator("button[type='reset']", "css", "重置按钮"),
        "form_error": Locator(".form-error", "css", "表单错误提示"),
        "required_field": Locator(".required", "css", "必填字段标记"),
        "success_message": Locator(".success-message", "css", "成功消息"),
    }
    
    # ========== 分页相关定位器 ==========
    PAGINATION = {
        "first_page": Locator(".pagination .first", "css", "首页"),
        "prev_page": Locator(".pagination .prev", "css", "上一页"),
        "next_page": Locator(".pagination .next", "css", "下一页"),
        "last_page": Locator(".pagination .last", "css", "末页"),
        "page_info": Locator(".pagination .info", "css", "页码信息"),
        "page_input": Locator(".pagination input", "css", "页码输入框"),
    }
    
    @classmethod
    def get_locator(cls, page_name: str, locator_name: str) -> Locator:
        """获取指定页面和名称的定位器"""
        page_locators = getattr(cls, page_name.upper(), cls.COMMON)
        if locator_name in page_locators:
            return page_locators[locator_name]
        elif locator_name in cls.COMMON:
            return cls.COMMON[locator_name]
        else:
            raise KeyError(f"Locator '{locator_name}' not found in '{page_name}' or COMMON")
    
    @classmethod
    def get_all_locators(cls, page_name: str) -> Dict[str, Locator]:
        """获取指定页面的所有定位器"""
        return getattr(cls, page_name.upper(), cls.COMMON)
    
    @classmethod
    def register_page_locators(cls, page_name: str, locators: Dict[str, Locator]):
        """动态注册页面定位器"""
        setattr(cls, page_name.upper(), locators)
