"""
日志配置模块
配置和管理自动化测试日志
"""
import os
import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from config.settings import settings


def setup_logger(
    name: str = "playwright_automation",
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    console: bool = True
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        log_file: 日志文件路径
        console: 是否输出到控制台
    
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 获取或创建logger
    logger = logging.getLogger(name)
    
    # 清除已存在的处理器
    logger.handlers.clear()
    
    # 设置日志级别
    level = level or settings.logging.level
    logger.setLevel(getattr(logging, level.upper()))
    
    # 日志格式
    formatter = logging.Formatter(
        settings.logging.format,
        datefmt=settings.logging.date_format
    )
    
    # 控制台处理器
    if console and settings.logging.console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 文件处理器
    if settings.logging.file:
        log_path = log_file or settings.logging.file_path
        log_dir = Path(log_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=settings.logging.max_bytes,
            backupCount=settings.logging.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称（可选）
    
    Returns:
        logging.Logger: 日志记录器
    """
    base_name = "playwright_automation"
    full_name = f"{base_name}.{name}" if name else base_name
    logger = logging.getLogger(full_name)
    
    # 如果logger没有处理器，进行初始化
    if not logger.handlers:
        logger = setup_logger(full_name)
    
    return logger


class LoggerContext:
    """日志上下文管理器"""
    
    def __init__(self, name: str, level: Optional[str] = None):
        self.name = name
        self.level = level
        self.logger = None
        self.original_level = None
    
    def __enter__(self):
        self.logger = get_logger(self.name)
        if self.level:
            self.original_level = self.logger.level
            self.logger.setLevel(getattr(logging, self.level.upper()))
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.original_level:
            self.logger.setLevel(self.original_level)


class TestLogger:
    """测试日志类"""
    
    _logger = None
    
    @classmethod
    def get_logger(cls):
        if cls._logger is None:
            cls._logger = setup_logger("test_execution")
        return cls._logger
    
    @classmethod
    def log_test_start(cls, test_name: str, params: dict = None):
        """记录测试开始"""
        logger = cls.get_logger()
        logger.info("=" * 60)
        logger.info(f"测试开始: {test_name}")
        if params:
            logger.info(f"测试参数: {params}")
        logger.info("=" * 60)
    
    @classmethod
    def log_test_end(cls, test_name: str, status: str, duration: float = None, error: str = None):
        """记录测试结束"""
        logger = cls.get_logger()
        logger.info("=" * 60)
        logger.info(f"测试结束: {test_name}")
        logger.info(f"测试状态: {status}")
        if duration:
            logger.info(f"执行时长: {duration:.2f}秒")
        if error:
            logger.error(f"错误信息: {error}")
        logger.info("=" * 60)
    
    @classmethod
    def log_step(cls, step_name: str, action: str, details: dict = None):
        """记录测试步骤"""
        logger = cls.get_logger()
        logger.info(f"[{step_name}] {action}")
        if details:
            for key, value in details.items():
                logger.info(f"  - {key}: {value}")
    
    @classmethod
    def log_screenshot(cls, path: str, description: str = ""):
        """记录截图"""
        logger = cls.get_logger()
        logger.info(f"截图已保存: {path}")
        if description:
            logger.info(f"截图描述: {description}")
    
    @classmethod
    def log_api_request(cls, method: str, url: str, headers: dict = None, body: any = None):
        """记录API请求"""
        logger = cls.get_logger()
        logger.info(f"API请求: {method} {url}")
        if headers:
            logger.debug(f"请求头: {headers}")
        if body:
            logger.debug(f"请求体: {body}")
    
    @classmethod
    def log_api_response(cls, status: int, body: any = None, duration: float = None):
        """记录API响应"""
        logger = cls.get_logger()
        logger.info(f"API响应: 状态码 {status}")
        if duration:
            logger.info(f"响应时间: {duration:.2f}秒")
        if body:
            logger.debug(f"响应体: {body}")


def log_decorator(func):
    """测试日志装饰器"""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.info(f"执行: {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"完成: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"失败: {func.__name__}, 错误: {e}")
            raise
    return wrapper


def step(step_name: str):
    """测试步骤装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            logger.info(f"[{step_name}] 开始")
            try:
                result = func(*args, **kwargs)
                logger.info(f"[{step_name}] 完成")
                return result
            except Exception as e:
                logger.error(f"[{step_name}] 失败: {e}")
                raise
        return wrapper
    return decorator
