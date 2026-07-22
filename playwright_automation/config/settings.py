"""
配置管理模块
支持多环境配置、浏览器设置、日志配置等
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


@dataclass
class BrowserConfig:
    """浏览器配置"""
    browser_type: str = "chromium"  # chromium, firefox, webkit
    headless: bool = False
    slow_mo: int = 0  # 慢动作延迟（毫秒）
    viewport: Dict[str, int] = field(default_factory=lambda: {"width": 1920, "height": 1080})
    user_agent: Optional[str] = None
    device_scale_factor: float = 1.0
    is_mobile: bool = False
    has_touch: bool = False
    args: list = field(default_factory=list)
    
    # 浏览器路径（可选）
    executable_path: Optional[str] = None
    
    # 下载设置
    downloads_path: Optional[str] = None
    
    # 代理设置
    proxy: Optional[Dict[str, str]] = None
    
    # 权限设置
    permissions: list = field(default_factory=list)


@dataclass
class TimeoutsConfig:
    """超时配置"""
    default: int = 30000  # 默认超时（毫秒）
    navigation: int = 30000  # 导航超时
    action: int = 10000  # 操作超时
    assertion: int = 5000  # 断言超时


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    console: bool = True
    file: bool = True
    file_path: str = "logs/automation.log"
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"


@dataclass
class ReportConfig:
    """报告配置"""
    enabled: bool = True
    screenshot_on_failure: bool = True
    video_on_failure: bool = False
    trace_on_failure: bool = True
    report_dir: str = "reports"
    screenshot_dir: str = "reports/screenshots"
    video_dir: str = "reports/videos"
    trace_dir: str = "reports/traces"


class Settings:
    """全局配置管理（单例模式）"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # 环境
        self.env = os.getenv("TEST_ENV", "dev")
        self.base_url = os.getenv("BASE_URL", "https://www.google.com")
        
        # 浏览器配置
        self.browser = BrowserConfig(
            browser_type=os.getenv("BROWSER_TYPE", "chromium"),
            headless=os.getenv("HEADLESS", "false").lower() == "true",
            slow_mo=int(os.getenv("SLOW_MO", "0")),
            executable_path=os.getenv("BROWSER_EXECUTABLE_PATH")
        )
        
        # 超时配置
        self.timeouts = TimeoutsConfig(
            default=int(os.getenv("TIMEOUT_DEFAULT", "30000")),
            navigation=int(os.getenv("TIMEOUT_NAVIGATION", "30000")),
            action=int(os.getenv("TIMEOUT_ACTION", "10000")),
            assertion=int(os.getenv("TIMEOUT_ASSERTION", "5000"))
        )
        
        # 日志配置
        self.logging = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            file_path=os.getenv("LOG_FILE", "logs/automation.log")
        )
        
        # 报告配置
        self.report = ReportConfig(
            enabled=os.getenv("REPORT_ENABLED", "true").lower() == "true",
            screenshot_on_failure=os.getenv("SCREENSHOT_ON_FAILURE", "true").lower() == "true",
            trace_on_failure=os.getenv("TRACE_ON_FAILURE", "true").lower() == "true"
        )
        
        # 凭证配置（可从环境变量或文件加载）
        self.credentials = self._load_credentials()
        
        self._initialized = True
    
    def _load_credentials(self) -> Dict[str, Any]:
        """从环境变量或配置文件加载凭证"""
        creds_file = Path("config/credentials.json")
        creds = {}
        
        if creds_file.exists():
            with open(creds_file, 'r', encoding='utf-8') as f:
                creds = json.load(f)
        
        # 环境变量优先级更高
        return {
            "username": os.getenv("TEST_USERNAME", creds.get("username", "")),
            "password": os.getenv("TEST_PASSWORD", creds.get("password", "")),
            "api_key": os.getenv("API_KEY", creds.get("api_key", ""))
        }
    
    def update_browser_config(self, **kwargs):
        """动态更新浏览器配置"""
        for key, value in kwargs.items():
            if hasattr(self.browser, key):
                setattr(self.browser, key, value)
    
    def update_timeouts(self, **kwargs):
        """动态更新超时配置"""
        for key, value in kwargs.items():
            if hasattr(self.timeouts, key):
                setattr(self.timeouts, key, value)
    
    def get_env_config(self, env_name: str) -> Optional[Dict[str, Any]]:
        """获取指定环境的配置"""
        env_file = Path(f"config/env_{env_name}.json")
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None


# 全局配置实例
settings = Settings()
