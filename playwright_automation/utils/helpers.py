"""
辅助工具函数
"""
import time
import random
import string
import functools
import logging
from typing import Any, Callable, Optional, List, Dict
from pathlib import Path
from datetime import datetime


def wait_for_condition(
    condition: Callable[[], bool],
    timeout: float = 10,
    interval: float = 0.5,
    message: str = "条件不满足"
) -> bool:
    """
    等待条件满足
    
    Args:
        condition: 条件函数
        timeout: 超时时间（秒）
        interval: 轮询间隔（秒）
        message: 超时消息
    
    Returns:
        bool: 条件是否满足
    """
    end_time = time.time() + timeout
    
    while time.time() < end_time:
        try:
            if condition():
                return True
        except Exception:
            pass
        time.sleep(interval)
    
    raise TimeoutError(message)


def retry(
    max_attempts: int = 3,
    delay: float = 1,
    backoff: float = 2,
    exceptions: tuple = (Exception,),
    logger: Optional[logging.Logger] = None
):
    """
    重试装饰器
    
    Args:
        max_attempts: 最大尝试次数
        delay: 初始延迟（秒）
        backoff: 延迟倍增因子
        exceptions: 需要重试的异常类型
        logger: 日志记录器
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        raise
                    
                    if logger:
                        logger.warning(
                            f"{func.__name__} 第 {attempt} 次尝试失败: {e}, "
                            f"{current_delay:.1f}秒后重试"
                        )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def capture_debug_info(page, include_screenshot: bool = True) -> Dict[str, Any]:
    """
    捕获调试信息
    
    Args:
        page: Playwright页面对象
        include_screenshot: 是否包含截图
    
    Returns:
        dict: 调试信息
    """
    debug_info = {
        "url": page.url,
        "title": page.title(),
        "timestamp": datetime.now().isoformat(),
    }
    
    # 添加截图
    if include_screenshot:
        try:
            screenshot_path = f"debug_screenshots/debug_{int(time.time())}.png"
            Path(screenshot_path).parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=screenshot_path)
            debug_info["screenshot"] = screenshot_path
        except Exception as e:
            debug_info["screenshot_error"] = str(e)
    
    # 添加控制台消息
    try:
        console_messages = []
        def handle_console(msg):
            console_messages.append({
                "type": msg.type,
                "text": msg.text
            })
        page.on("console", handle_console)
        debug_info["console_messages"] = console_messages
    except Exception as e:
        debug_info["console_error"] = str(e)
    
    return debug_info


def generate_random_string(length: int = 10, include_digits: bool = True, include_special: bool = False) -> str:
    """
    生成随机字符串
    
    Args:
        length: 字符串长度
        include_digits: 包含数字
        include_special: 包含特殊字符
    
    Returns:
        str: 随机字符串
    """
    chars = string.ascii_letters
    
    if include_digits:
        chars += string.digits
    
    if include_special:
        chars += string.punctuation
    
    return ''.join(random.choice(chars) for _ in range(length))


def generate_random_email(domain: str = "test.com") -> str:
    """生成随机邮箱"""
    username = generate_random_string(random.randint(5, 10))
    return f"{username}@{domain}"


def generate_random_phone(country_code: str = "86") -> str:
    """生成随机手机号"""
    if country_code == "86":
        # 中国手机号格式
        prefixes = ['130', '131', '132', '133', '134', '135', '136', '137', '138', '139',
                   '150', '151', '152', '153', '155', '156', '157', '158', '159',
                   '180', '181', '182', '183', '184', '185', '186', '187', '188', '189']
        prefix = random.choice(prefixes)
        suffix = ''.join([str(random.randint(0, 9)) for _ in range(8)])
        return f"+{country_code}{prefix}{suffix}"
    else:
        return f"+{country_code}{generate_random_string(10, include_digits=True)}"


def format_timestamp(timestamp: float = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化时间戳"""
    if timestamp is None:
        timestamp = time.time()
    return datetime.fromtimestamp(timestamp).strftime(format_str)


def safe_get(data: dict, *keys, default: Any = None) -> Any:
    """
    安全获取字典值
    
    Args:
        data: 字典
        *keys: 嵌套键
        default: 默认值
    
    Returns:
        Any: 获取的值
    """
    result = data
    for key in keys:
        try:
            result = result[key]
        except (KeyError, TypeError, IndexError):
            return default
    return result


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """将列表分块"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def read_json_file(file_path: str) -> Dict:
    """读取JSON文件"""
    import json
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json_file(file_path: str, data: Dict, indent: int = 2):
    """写入JSON文件"""
    import json
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def read_yaml_file(file_path: str) -> Dict:
    """读取YAML文件"""
    import yaml
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def write_yaml_file(file_path: str, data: Dict):
    """写入YAML文件"""
    import yaml
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)


class Timer:
    """计时器"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.elapsed = 0
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.stop()
    
    def start(self):
        self.start_time = time.time()
        return self
    
    def stop(self):
        self.end_time = time.time()
        self.elapsed = self.end_time - self.start_time
        return self.elapsed
    
    def reset(self):
        self.start_time = None
        self.end_time = None
        self.elapsed = 0


class RateLimiter:
    """速率限制器"""
    
    def __init__(self, max_calls: int, period: float):
        """
        Args:
            max_calls: 最大调用次数
            period: 时间段（秒）
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = []
    
    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self._wait_if_needed()
            result = func(*args, **kwargs)
            self.calls.append(time.time())
            return result
        return wrapper
    
    def _wait_if_needed(self):
        now = time.time()
        # 清理过期的调用记录
        self.calls = [t for t in self.calls if now - t < self.period]
        
        # 如果达到限制，等待
        if len(self.calls) >= self.max_calls:
            sleep_time = self.period - (now - self.calls[0])
            if sleep_time > 0:
                time.sleep(sleep_time)


def calculate_checksum(file_path: str, algorithm: str = "md5") -> str:
    """计算文件校验和"""
    import hashlib
    
    hash_func = getattr(hashlib, algorithm)()
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def compare_dicts(dict1: Dict, dict2: Dict, ignore_keys: List[str] = None) -> Dict[str, Any]:
    """
    比较两个字典的差异
    
    Args:
        dict1: 字典1
        dict2: 字典2
        ignore_keys: 忽略的键列表
    
    Returns:
        dict: 差异信息
    """
    ignore_keys = ignore_keys or []
    diff = {
        "added": {},
        "removed": {},
        "changed": {},
        "equal": {}
    }
    
    all_keys = set(dict1.keys()) | set(dict2.keys())
    
    for key in all_keys:
        if key in ignore_keys:
            continue
        
        if key not in dict1:
            diff["added"][key] = dict2[key]
        elif key not in dict2:
            diff["removed"][key] = dict1[key]
        elif dict1[key] != dict2[key]:
            diff["changed"][key] = {
                "old": dict1[key],
                "new": dict2[key]
            }
        else:
            diff["equal"][key] = dict1[key]
    
    return diff
