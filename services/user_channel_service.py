"""
用户渠道管理服务
提供修改用户注册渠道的功能
"""
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class UserChannelService:
    """用户渠道管理服务"""

    def __init__(self, db_manager):
        """
        初始化服务

        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager

    def get_user_by_mobile(self, mobile: str, country_code: str = '86') -> Optional[Dict[str, Any]]:
        """
        通过手机号查询用户信息

        Args:
            mobile: 手机号
            country_code: 国家代码，默认86

        Returns:
            用户信息字典，如果未找到则返回None
        """
        try:
            sql = """
            SELECT nn_id, mobile_num, src_channel, nickname, create_time, public_ip, is_pay_user
            FROM `leigod_config`.`tbl_user` 
            WHERE `mobile_num` = %s AND `country_code` = %s
            LIMIT 1
            """
            params = (mobile, country_code)

            with self.db_manager.get_cursor() as cursor:
                cursor.execute(sql, params)
                result = cursor.fetchone()

            return result
        except Exception as e:
            logger.error(f"查询用户信息失败: {str(e)}")
            return None

    def get_user_by_nn_id(self, nn_id: str) -> Optional[Dict[str, Any]]:
        """
        通过NN ID查询用户信息

        Args:
            nn_id: NN ID

        Returns:
            用户信息字典，如果未找到则返回None
        """
        try:
            sql = """
            SELECT nn_id, mobile_num, src_channel, nickname, create_time, public_ip, is_pay_user
            FROM `leigod_config`.`tbl_user` 
            WHERE `nn_id` = %s
            LIMIT 1
            """
            params = (nn_id,)

            with self.db_manager.get_cursor() as cursor:
                cursor.execute(sql, params)
                result = cursor.fetchone()

            return result
        except Exception as e:
            logger.error(f"查询用户信息失败: {str(e)}")
            return None

    def update_user_channel(self, nn_id: str, new_channel: str) -> Dict[str, Any]:
        """
        修改用户注册渠道

        Args:
            nn_id: 用户NN ID
            new_channel: 新的注册渠道

        Returns:
            操作结果字典
        """
        try:
            # 首先检查用户是否存在
            user_info = self.get_user_by_nn_id(nn_id)
            if not user_info:
                return {
                    'success': False,
                    'error': '用户不存在',
                    'code': 'USER_NOT_FOUND'
                }

            # 更新用户的注册渠道
            sql = """
            UPDATE `leigod_config`.`tbl_user` 
            SET `src_channel` = %s, `change_time` = %s
            WHERE `nn_id` = %s
            """
            params = (new_channel, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), nn_id)

            with self.db_manager.get_cursor() as cursor:
                cursor.execute(sql, params)
                affected_rows = cursor.rowcount

            if affected_rows > 0:
                logger.info(f"用户 {nn_id} 的注册渠道已更新为 {new_channel}")
                return {
                    'success': True,
                    'message': '用户注册渠道更新成功',
                    'data': {
                        'nn_id': nn_id,
                        'old_channel': user_info['src_channel'],
                        'new_channel': new_channel,
                        'updated_at': datetime.now().isoformat()
                    }
                }
            else:
                return {
                    'success': False,
                    'error': '更新失败',
                    'code': 'UPDATE_FAILED'
                }

        except Exception as e:
            logger.error(f"更新用户渠道失败: {str(e)}")
            return {
                'success': False,
                'error': f'更新失败: {str(e)}',
                'code': 'DATABASE_ERROR'
            }

    def update_user_channel_by_mobile(self, mobile: str, country_code: str, new_channel: str) -> Dict[str, Any]:
        """
        通过手机号修改用户注册渠道

        Args:
            mobile: 手机号
            country_code: 国家代码
            new_channel: 新的注册渠道

        Returns:
            操作结果字典
        """
        try:
            # 首先通过手机号查询用户
            user_info = self.get_user_by_mobile(mobile, country_code)
            if not user_info:
                return {
                    'success': False,
                    'error': '用户不存在',
                    'code': 'USER_NOT_FOUND'
                }

            # 更新用户的注册渠道
            return self.update_user_channel(user_info['nn_id'], new_channel)

        except Exception as e:
            logger.error(f"通过手机号更新用户渠道失败: {str(e)}")
            return {
                'success': False,
                'error': f'更新失败: {str(e)}',
                'code': 'DATABASE_ERROR'
            }

    def update_user_register_time(self, user_id: str, new_create_time: str) -> Dict[str, Any]:
        """
        修改用户注册时间
        
        Args:
            user_id: 用户ID
            new_create_time: 新的注册时间 (YYYY-MM-DD HH:MM:SS格式)
        
        Returns:
            操作结果字典
        """
        try:
            # 首先检查用户是否存在
            sql_check = """
            SELECT id, create_time 
            FROM `leigod_config`.`tbl_user` 
            WHERE `id` = %s
            LIMIT 1
            """
            
            with self.db_manager.get_cursor() as cursor:
                cursor.execute(sql_check, (user_id,))
                user_info = cursor.fetchone()
                
            if not user_info:
                return {
                    'success': False,
                    'message': '用户不存在',
                    'code': 'USER_NOT_FOUND'
                }
            
            # 更新用户的注册时间
            sql_update = """
            UPDATE `leigod_config`.`tbl_user` 
            SET `create_time` = %s
            WHERE `id` = %s
            """
            
            with self.db_manager.get_cursor() as cursor:
                cursor.execute(sql_update, (new_create_time, user_id))
                affected_rows = cursor.rowcount
                logger.info(f"注册时间更新SQL执行影响行数: {affected_rows}")
                
                # 如果没有影响行数，检查是否是因为数据已经是目标状态
                if affected_rows == 0:
                    # 检查当前注册时间
                    check_current_sql = "SELECT create_time FROM `leigod_config`.`tbl_user` WHERE `id` = %s"
                    cursor.execute(check_current_sql, (user_id,))
                    current_result = cursor.fetchone()
                    
                    if current_result:
                        current_create_time = current_result['create_time']
                        # 比较时间（处理datetime对象和字符串）
                        if hasattr(current_create_time, 'strftime'):
                            current_time_str = current_create_time.strftime('%Y-%m-%d %H:%M:%S')
                            times_equal = (current_time_str == new_create_time)
                        else:
                            times_equal = (str(current_create_time) == new_create_time)
                        
                        if times_equal:
                            logger.info(f"用户 {user_id} 的注册时间已经是目标时间: {new_create_time}")
                            return {
                                'success': True,
                                'message': '用户注册时间已是目标时间，无需更新',
                                'data': {
                                    'user_id': user_id,
                                    'old_create_time': user_info['create_time'],
                                    'new_create_time': new_create_time,
                                    'updated_at': datetime.now().isoformat()
                                }
                            }
            
            if affected_rows > 0:
                logger.info(f"用户 {user_id} 的注册时间已更新为 {new_create_time}")
                return {
                    'success': True,
                    'message': '用户注册时间更新成功',
                    'data': {
                        'user_id': user_id,
                        'old_create_time': user_info['create_time'],
                        'new_create_time': new_create_time,
                        'updated_at': datetime.now().isoformat()
                    }
                }
            else:
                return {
                    'success': False,
                    'message': '更新失败，可能没有符合条件的记录',
                    'code': 'UPDATE_FAILED'
                }
                
        except Exception as e:
            logger.error(f"更新用户注册时间失败: {str(e)}")
            return {
                'success': False,
                'message': f'更新失败: {str(e)}',
                'code': 'DATABASE_ERROR'
            }

    def update_user_payment_status(self, user_id: str, first_pay_time: Optional[str]) -> Dict[str, Any]:
        """
        修改用户付费状态
        
        Args:
            user_id: 用户ID
            first_pay_time: 首次付费时间 (YYYY-MM-DD HH:MM:SS格式或None表示未付费)
        
        Returns:
            操作结果字典
        """
        try:
            # 首先检查用户是否存在
            sql_check = """
            SELECT id, first_pay_time, is_pay_user
            FROM `leigod_config`.`tbl_user` 
            WHERE `id` = %s
            LIMIT 1
            """
            
            logger.info(f"正在查询用户 {user_id} 是否存在...")
            
            with self.db_manager.get_cursor() as cursor:
                cursor.execute(sql_check, (user_id,))
                user_info = cursor.fetchone()
                
            if not user_info:
                # 如果在leigod_config中没找到，尝试在其他可能的数据库中查找
                logger.warning(f"在leigod_config.tbl_user中未找到用户 {user_id}，尝试其他数据库...")
                
                # 检查当前连接的数据库
                with self.db_manager.get_cursor() as cursor:
                    cursor.execute("SELECT DATABASE()")
                    current_db = cursor.fetchone()
                    logger.info(f"当前连接的数据库: {current_db}")
                    
                    # 列出所有可用的数据库
                    cursor.execute("SHOW DATABASES LIKE 'leigod_%'")
                    databases = cursor.fetchall()
                    logger.info(f"可用的leigod数据库: {databases}")
                    
                    # 在每个数据库中查找该用户
                    for db_row in databases:
                        db_name = db_row[0]
                        check_sql = f"SELECT id, first_pay_time, is_pay_user FROM `{db_name}`.`tbl_user` WHERE `id` = %s LIMIT 1"
                        try:
                            cursor.execute(check_sql, (user_id,))
                            found_user = cursor.fetchone()
                            if found_user:
                                logger.info(f"在数据库 {db_name} 中找到了用户 {user_id}")
                                user_info = found_user
                                break
                        except Exception as db_error:
                            logger.warning(f"在数据库 {db_name} 中查询失败: {db_error}")
                
                if not user_info:
                    return {
                        'success': False,
                        'message': f'用户不存在，ID: {user_id} 在任何数据库中都未找到',
                        'code': 'USER_NOT_FOUND'
                    }
            
            # 更新用户的付费状态
            # 先检查用户当前状态
            logger.info(f"用户当前状态: id={user_info['id']}, first_pay_time={user_info['first_pay_time']}, is_pay_user={user_info['is_pay_user']}")
            
            # 构造更新SQL，一次性更新两个字段
            if first_pay_time is None:
                sql_update = """
                UPDATE `leigod_config`.`tbl_user` 
                SET `first_pay_time` = NULL, `is_pay_user` = 0
                WHERE `id` = %s
                """
                params = (user_id,)
                logger.info("执行NULL值更新SQL")
            else:
                sql_update = """
                UPDATE `leigod_config`.`tbl_user` 
                SET `first_pay_time` = %s, `is_pay_user` = 1
                WHERE `id` = %s
                """
                params = (first_pay_time, user_id)
                logger.info(f"执行非NULL值更新SQL，first_pay_time={first_pay_time}")
            
            logger.info(f"准备更新用户付费状态: user_id={user_id}, first_pay_time={first_pay_time}, is_pay_user={1 if first_pay_time is not None else 0}")
            logger.info(f"SQL语句: {sql_update.strip()}")
            logger.info(f"参数: {params}")
            
            with self.db_manager.get_cursor() as cursor:
                cursor.execute(sql_update, params)
                affected_rows = cursor.rowcount
                logger.info(f"SQL执行影响行数: {affected_rows}")
                
                # 如果没有影响行数，先检查是否是因为数据已经是目标状态
                if affected_rows == 0:
                    # 检查是否是因为数据已经是目标状态
                    current_is_pay_user = 1 if user_info['first_pay_time'] is not None else 0
                    target_is_pay_user = 1 if first_pay_time is not None else 0
                    
                    # 处理时间比较（考虑datetime对象和字符串的比较）
                    current_first_pay_time = user_info['first_pay_time']
                    times_equal = False
                    
                    if first_pay_time is None and current_first_pay_time is None:
                        times_equal = True
                    elif first_pay_time is not None and current_first_pay_time is not None:
                        # 如果current_first_pay_time是datetime对象，转换为字符串比较
                        if hasattr(current_first_pay_time, 'strftime'):
                            current_time_str = current_first_pay_time.strftime('%Y-%m-%d %H:%M:%S')
                            times_equal = (current_time_str == first_pay_time)
                        else:
                            times_equal = (str(current_first_pay_time) == first_pay_time)
                    
                    if current_is_pay_user == target_is_pay_user and times_equal:
                        logger.info(f"用户 {user_id} 的付费状态已经是目标状态: first_pay_time={first_pay_time}, is_pay_user={target_is_pay_user}")
                        return {
                            'success': True,
                            'message': '用户付费状态已是目标状态，无需更新',
                            'data': {
                                'user_id': user_id,
                                'old_first_pay_time': user_info['first_pay_time'],
                                'new_first_pay_time': first_pay_time,
                                'old_is_pay_user': user_info['is_pay_user'],
                                'new_is_pay_user': target_is_pay_user,
                                'updated_at': datetime.now().isoformat()
                            }
                        }
                    
                    # 如果不是状态重复，则进行详细诊断
                    logger.warning("首次更新未影响任何行，尝试检查WHERE条件...")
                    # 检查用户是否真的存在
                    check_sql = "SELECT id, first_pay_time, is_pay_user FROM `leigod_config`.`tbl_user` WHERE `id` = %s"
                    cursor.execute(check_sql, (user_id,))
                    verify_user = cursor.fetchone()
                    logger.info(f"验证查询结果: {verify_user}")
                    
                    # 尝试更简单的更新语句来诊断问题
                    logger.info("尝试诊断性更新...")
                    diagnostic_sql = "UPDATE `leigod_config`.`tbl_user` SET `is_pay_user` = `is_pay_user` WHERE `id` = %s"
                    cursor.execute(diagnostic_sql, (user_id,))
                    diagnostic_affected = cursor.rowcount
                    logger.info(f"诊断性更新影响行数: {diagnostic_affected}")
                    
                    # 检查表结构
                    if diagnostic_affected == 0:
                        logger.warning("即使是诊断性更新也失败了，检查表结构...")
                        
                        # 检查当前连接的用户权限
                        cursor.execute("SELECT USER(), DATABASE(), CONNECTION_ID()")
                        connection_info = cursor.fetchone()
                        logger.info(f"连接信息: {connection_info}")
                        
                        # 检查用户权限
                        cursor.execute("""
                        SELECT COLUMN_NAME, PRIVILEGE_TYPE 
                        FROM INFORMATION_SCHEMA.COLUMN_PRIVILEGES 
                        WHERE TABLE_SCHEMA = 'leigod_config' 
                        AND TABLE_NAME = 'tbl_user' 
                        AND COLUMN_NAME IN ('first_pay_time', 'is_pay_user')
                        """)
                        column_privileges = cursor.fetchall()
                        logger.info(f"字段权限: {column_privileges}")
                        
                        # 检查全局权限
                        cursor.execute("SHOW GRANTS")
                        grants = cursor.fetchall()
                        logger.info(f"用户权限: {[grant[0] for grant in grants]}")
                        
                        cursor.execute("DESCRIBE `leigod_config`.`tbl_user`")
                        table_structure = cursor.fetchall()
                        logger.info(f"表结构: {[(col[0], col[1]) for col in table_structure]}")
                        
                        # 检查是否有触发器
                        cursor.execute("""
                        SELECT TRIGGER_NAME, EVENT_MANIPULATION, ACTION_TIMING 
                        FROM INFORMATION_SCHEMA.TRIGGERS 
                        WHERE EVENT_OBJECT_TABLE = 'tbl_user' AND EVENT_OBJECT_SCHEMA = 'leigod_config'
                        """)
                        triggers = cursor.fetchall()
                        logger.info(f"相关触发器: {triggers}")
                        
                        # 尝试INSERT一个测试记录来验证写权限
                        try:
                            test_insert_sql = """
                            INSERT INTO `leigod_config`.`tbl_user` 
                            (`id`, `mobile_num`, `country_code`, `create_time`) 
                            VALUES (%s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE `create_time` = VALUES(`create_time`)
                            """
                            test_params = (999999999, '13800138000', '86', '2026-01-01 00:00:00')
                            cursor.execute(test_insert_sql, test_params)
                            insert_affected = cursor.rowcount
                            logger.info(f"测试插入影响行数: {insert_affected}")
                            
                            # 回滚测试数据
                            cursor.execute("DELETE FROM `leigod_config`.`tbl_user` WHERE `id` = 999999999")
                            
                        except Exception as insert_error:
                            logger.error(f"测试插入失败: {insert_error}")
            
            if affected_rows > 0:
                logger.info(f"用户 {user_id} 的付费状态已更新为 first_pay_time={first_pay_time}, is_pay_user={1 if first_pay_time is not None else 0}")
                return {
                    'success': True,
                    'message': '用户付费状态更新成功',
                    'data': {
                        'user_id': user_id,
                        'old_first_pay_time': user_info['first_pay_time'],
                        'new_first_pay_time': first_pay_time,
                        'old_is_pay_user': user_info['is_pay_user'],
                        'new_is_pay_user': 1 if first_pay_time is not None else 0,
                        'updated_at': datetime.now().isoformat()
                    }
                }
            else:
                # 这里不应该到达，因为上面已经处理了affected_rows == 0的情况
                logger.warning(f"更新失败，没有找到用户ID为 {user_id} 的记录")
                return {
                    'success': False,
                    'message': f'更新失败，用户ID {user_id} 不存在或没有符合条件的记录',
                    'code': 'UPDATE_FAILED'
                }
                
        except Exception as e:
            logger.error(f"更新用户付费状态失败: {str(e)}")
            return {
                'success': False,
                'message': f'更新失败: {str(e)}',
                'code': 'DATABASE_ERROR'
            }

    def format_update_response(
        self,
        result: Dict[str, Any],
        operation_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        格式化更新响应

        Args:
            result: 操作结果
            operation_params: 操作参数

        Returns:
            格式化的响应字典
        """
        response = {
            'success': result['success'],
            'operation_info': operation_params,
            'timestamp': datetime.now().isoformat()
        }

        if result['success']:
            response['data'] = result.get('data', {})
            response['message'] = result.get('message', '操作成功')
        else:
            response['error'] = result.get('error', '未知错误')
            response['code'] = result.get('code', 'UNKNOWN_ERROR')

        return response