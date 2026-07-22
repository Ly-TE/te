"""
数据库连接管理模块 - 放在DB目录下
支持连接池和不同环境配置
"""
import os
import sys
import pymysql
from pymysql import cursors
from dbutils.pooled_db import PooledDB
from typing import Optional, List, Dict, Any, Tuple
import logging
from contextlib import contextmanager

# 添加父目录到系统路径，确保可以正确导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入配置文件
try:
    from config.db import config  # 从config目录导入
except ImportError:
    # 如果直接运行，尝试另一种导入方式
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from config.db import config

# 配置日志
logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理类 - 支持懒加载"""

    def __init__(self):
        """初始化数据库连接池管理器（不立即连接）"""
        self._pools = {}
        # 改为懒加载，不在这里初始化连接池

    def _get_or_create_pool(self, env: str = None) -> PooledDB:
        """获取或创建连接池（懒加载）"""
        if env is None:
            env = config.ENV

        env = env.lower()

        # 如果连接池不存在，创建它
        if env not in self._pools:
            try:
                db_config = config.DATABASES[env]
                pool_config = {
                    'creator': pymysql,
                    'maxconnections': db_config.pool_size,
                    'mincached': 1,
                    'maxcached': 3,
                    'blocking': True,
                    'ping': 1,
                    'host': db_config.host,
                    'port': db_config.port,
                    'user': db_config.user,
                    'password': db_config.password,
                    'charset': db_config.charset,
                    'cursorclass': cursors.DictCursor,
                    'autocommit': False
                }

                # 只有database不为None且不为空时才添加
                if db_config.database:
                    pool_config['database'] = db_config.database

                pool = PooledDB(**pool_config)
                self._pools[env] = pool
                logger.info(f"数据库连接池创建成功: {env} (数据库: {db_config.database or '无默认数据库'})")
            except Exception as e:
                logger.error(f"数据库连接池创建失败 {env}: {str(e)}")
                raise

        return self._pools[env]

    @contextmanager
    def get_connection(self, env: str = None):
        """获取数据库连接（上下文管理器）"""
        pool = self._get_or_create_pool(env)
        conn = None

        try:
            conn = pool.connection()
            logger.debug(f"获取数据库连接成功: {env}")
            yield conn
            conn.commit()
        except pymysql.err.OperationalError as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            logger.error(f"数据库操作失败（连接错误）: {str(e)}")
            # 抛出更友好的错误信息
            raise ConnectionError(f"无法连接到数据库服务器。请检查：\n"
                                  f"1. MySQL服务是否启动\n"
                                  f"2. 主机地址: {config.DATABASES.get(env or config.ENV, {}).get('host', 'unknown')}\n"
                                  f"3. 端口: {config.DATABASES.get(env or config.ENV, {}).get('port', 'unknown')}\n"
                                  f"4. 错误详情: {str(e)}")
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            logger.error(f"数据库操作失败: {str(e)}")
            raise
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass

    @contextmanager
    def get_cursor(self, env: str = None):
        """获取数据库游标（上下文管理器）"""
        with self.get_connection(env) as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()

    def execute_query(self, sql: str, params: Tuple = None, env: str = None) -> List[Dict[str, Any]]:
        """执行查询语句"""
        try:
            with self.get_cursor(env) as cursor:
                cursor.execute(sql, params or ())
                return cursor.fetchall()
        except ConnectionError as e:
            # 返回空结果，而不是抛出异常
            logger.warning(f"数据库连接失败，返回空结果: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"查询执行失败: {str(e)}")
            raise

    def query_paginate(self, sql: str, page: int = 1, page_size: int = None,
                       params: Tuple = None, env: str = None) -> Dict[str, Any]:
        """分页查询"""
        try:
            if page_size is None:
                page_size = config.DEFAULT_PAGE_SIZE

            # 限制最大页大小
            page_size = min(page_size, config.MAX_PAGE_SIZE)

            # 计算偏移量
            offset = (page - 1) * page_size

            # 构建分页SQL
            paginated_sql = f"{sql} LIMIT %s OFFSET %s"
            paginated_params = (*(params or ()), page_size, offset)

            # 查询数据
            with self.get_cursor(env) as cursor:
                cursor.execute(paginated_sql, paginated_params)
                results = cursor.fetchall()

                # 查询总数
                try:
                    count_sql = f"SELECT COUNT(*) as total FROM ({sql}) as count_table"
                    cursor.execute(count_sql, params or ())
                    total_result = cursor.fetchone()
                    total = total_result['total'] if total_result else 0
                except:
                    total = len(results)

                return {
                    'items': results,
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total + page_size - 1) // page_size if page_size > 0 else 0
                }

        except ConnectionError as e:
            logger.warning(f"数据库连接失败，返回空分页结果: {str(e)}")
            return {
                'items': [],
                'total': 0,
                'page': page,
                'page_size': page_size or config.DEFAULT_PAGE_SIZE,
                'total_pages': 0
            }

    def health_check(self, env: str = None) -> bool:
        """数据库健康检查"""
        try:
            with self.get_connection(env) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    return result is not None
        except Exception as e:
            logger.warning(f"数据库健康检查失败: {str(e)}")
            return False

    def close_all(self):
        """关闭所有连接池"""
        for env, pool in self._pools.items():
            try:
                pool.close()
                logger.info(f"关闭连接池: {env}")
            except Exception as e:
                logger.error(f"关闭连接池失败 {env}: {str(e)}")
        self._pools.clear()


# 创建全局数据库管理器实例 - 确保这一行存在
db_manager = DatabaseManager()

# 确保导出 - 添加这一行
__all__ = ['DatabaseManager', 'db_manager']