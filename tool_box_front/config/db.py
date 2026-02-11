"""
数据库配置文件 - 放在config目录下
支持不同环境的配置
"""
import os
import sys
from typing import Dict, Any, Optional  # 添加 Optional 导入
from dataclasses import dataclass
from dotenv import load_dotenv

# 添加父目录到系统路径，确保可以正确导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
load_dotenv()

@dataclass
class DatabaseConfig:
    """数据库配置类"""
    host: str
    port: int
    user: str
    password: str
    database: Optional[str] = None  # 改为可选参数
    charset: str = "utf8mb4"
    pool_size: int = 5
    pool_recycle: int = 3600

class DBConfig:
    """配置基类"""
    # 调试模式
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'

    # 数据库配置
    DATABASES: Dict[str, DatabaseConfig] = {
        # 开发环境
        'development': DatabaseConfig(
            host=os.getenv('DEV_DB_HOST', 'localhost'),
            port=int(os.getenv('DEV_DB_PORT', 3306)),
            user=os.getenv('DEV_DB_USER', 'root'),
            password=os.getenv('DEV_DB_PASSWORD', ''),
            database=os.getenv('DEV_DB_NAME', None),
            charset=os.getenv('DEV_DB_CHARSET', 'utf8mb4')
        ),

        # 测试环境
        'testing': DatabaseConfig(
            host=os.getenv('TEST_DB_HOST', '123.60.66.91'),
            port=int(os.getenv('TEST_DB_PORT', 33506)),
            user=os.getenv('TEST_DB_USER', 'leigod_pre_w'),
            password=os.getenv('TEST_DB_PASSWORD', 'VgLaQcyoheXpsx'),
            database='leigod_config',  # 指定正确的数据库
            charset=os.getenv('TEST_DB_CHARSET', 'utf8mb4')
        ),

        # 生产环境
        'production': DatabaseConfig(
            host=os.getenv('PROD_DB_HOST', 'localhost'),
            port=int(os.getenv('PROD_DB_PORT', 3306)),
            user=os.getenv('PROD_DB_USER', 'root'),
            password=os.getenv('PROD_DB_PASSWORD', ''),
            database=os.getenv('PROD_DB_NAME', None),
            charset=os.getenv('PROD_DB_CHARSET', 'utf8mb4')
        )
    }

    # 当前环境
    ENV: str = os.getenv('ENVIRONMENT', 'testing')

    # 获取当前环境的数据库配置
    @property
    def db_config(self) -> DatabaseConfig:
        """获取当前环境的数据库配置"""
        env = self.ENV.lower()
        if env not in self.DATABASES:
            raise ValueError(f"未找到环境配置: {env}")
        return self.DATABASES[env]

    # 安全配置
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'your-secret-key-here')

    # API配置
    API_PREFIX: str = '/api/v1'

    # 分页配置
    DEFAULT_PAGE_SIZE: int = int(os.getenv('DEFAULT_PAGE_SIZE', 100))
    MAX_PAGE_SIZE: int = int(os.getenv('MAX_PAGE_SIZE', 1000))

# 创建配置实例
config = DBConfig()

# 使用示例
if __name__ == "__main__":
    print(f"当前环境: {config.ENV}")
    print(f"数据库配置: {config.db_config}")
    print(f"数据库名: {config.db_config.database or '未指定，查询时动态指定'}")