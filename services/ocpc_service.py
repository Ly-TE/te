"""
OCPC查询服务
提供OCPC相关的数据查询功能
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class OCPCQueryBuilder:
    """OCPC查询构建器"""
    
    # 支持的表名映射
    TABLE_MAPPING = {
        'ocpc_mapping': 'tbl_ocpc_mapping',
        'ocpc_log': 'tbl_ocpc_log',
    }
    
    # 允许的排序方向
    ALLOWED_ORDERS = ['asc', 'desc']
    
    def __init__(self, table_name: str):
        """
        初始化查询构建器
        
        Args:
            table_name: 表名(ocpc_mapping 或 ocpc_log)
        """
        if table_name not in self.TABLE_MAPPING:
            raise ValueError(f"不支持的表名: {table_name}")
        
        self.table_name = self.TABLE_MAPPING[table_name]
        self.conditions = []
        self.params = []
        self.order_by = None
    
    def add_channel_filter(self, channel: str) -> 'OCPCQueryBuilder':
        """添加渠道过滤条件"""
        if channel:
            self.conditions.append("`channel` = %s")
            self.params.append(channel)
        return self
    
    def add_time_range_filter(
        self, 
        start_time: Optional[str] = None, 
        end_time: Optional[str] = None
    ) -> 'OCPCQueryBuilder':
        """添加时间范围过滤条件"""
        if start_time:
            self.conditions.append("`create_time` >= %s")
            self.params.append(start_time)
        
        if end_time:
            self.conditions.append("`create_time` <= %s")
            self.params.append(end_time)
        
        return self
    
    def set_order(self, order: str = 'desc') -> 'OCPCQueryBuilder':
        """设置排序方式"""
        order_lower = order.lower()
        if order_lower not in self.ALLOWED_ORDERS:
            order_lower = 'desc'
        self.order_by = f"ORDER BY `create_time` {order_lower.upper()}"
        return self
    
    def build(self) -> Tuple[str, tuple]:
        """
        构建SQL查询
        
        Returns:
            (SQL语句, 参数元组)
        """
        sql_parts = [f"SELECT * FROM `{self.table_name}`"]
        
        if self.conditions:
            sql_parts.append("WHERE " + " AND ".join(self.conditions))
        
        if self.order_by:
            sql_parts.append(self.order_by)
        
        sql = " ".join(sql_parts)
        return sql, tuple(self.params)


class OCPCService:
    """OCPC查询服务"""
    
    def __init__(self, db_manager):
        """
        初始化服务
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager
    
    def validate_query_params(
        self, 
        channel: Optional[str] = None,
        table: Optional[str] = None,
        **kwargs
    ) -> Tuple[bool, Optional[str]]:
        """
        验证查询参数
        
        Returns:
            (是否有效, 错误信息)
        """
        if channel is not None and not channel:
            return False, "channel参数不能为空"
        
        if table and table not in OCPCQueryBuilder.TABLE_MAPPING:
            return False, f"table参数必须是: {', '.join(OCPCQueryBuilder.TABLE_MAPPING.keys())}"
        
        return True, None
    
    def query_table(
        self,
        table_name: str,
        channel: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        order: str = 'desc',
        page: int = 1,
        page_size: int = 20,
        env: str = 'production'
    ) -> Dict[str, Any]:
        """
        查询OCPC表数据
        
        Args:
            table_name: 表名(ocpc_mapping 或 ocpc_log)
            channel: 渠道名称
            start_time: 开始时间
            end_time: 结束时间
            order: 排序方式(asc/desc)
            page: 页码
            page_size: 每页数量
            env: 环境
            
        Returns:
            查询结果字典
        """
        # 验证参数
        is_valid, error_msg = self.validate_query_params(channel=channel, table=table_name)
        if not is_valid:
            raise ValueError(error_msg)
        
        # 构建查询
        builder = OCPCQueryBuilder(table_name)
        sql, params = (builder
                      .add_channel_filter(channel)
                      .add_time_range_filter(start_time, end_time)
                      .set_order(order)
                      .build())
        
        # 为OCPC查询使用专门的数据库环境
        ocpc_env = f"{env}_ocpc" if not env.endswith('_ocpc') else env
                
        #执行分页查询
        result = self.db_manager.query_paginate(
            sql=sql,
            params=params,
            page=page,
            page_size=page_size,
            env=ocpc_env
        )
        
        return result
    
    def format_query_response(
        self,
        result: Dict[str, Any],
        query_params: Dict[str, Any],
        rate_limit_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        格式化查询响应
        
        Args:
            result: 查询结果
            query_params: 查询参数
            rate_limit_info: 频率限制信息
            
        Returns:
            格式化的响应字典
        """
        response = {
            'success': True,
            'data': result['items'],
            'pagination': {
                'page': result['page'],
                'page_size': result['page_size'],
                'total': result['total'],
                'total_pages': result['total_pages']
            },
            'query_info': query_params,
            'timestamp': datetime.now().isoformat()
        }
        
        if rate_limit_info:
            response['rate_limit_info'] = rate_limit_info
        
        return response
    
    def batch_query(
        self,
        queries: List[Dict[str, Any]],
        env: str = 'production'
    ) -> List[Dict[str, Any]]:
        """
        批量查询
        
        Args:
            queries: 查询列表
            env: 环境
            
        Returns:
            查询结果列表
        """
        results = []
        
        for i, query in enumerate(queries):
            try:
                table = query.get('table')
                channel = query.get('channel')
                start_time = query.get('start_time')
                end_time = query.get('end_time')
                order = query.get('order', 'desc')
                
                # 验证参数
                if not table or not channel:
                    results.append({
                        'success': False,
                        'error': f'第{i + 1}个查询缺少table或channel参数',
                        'index': i
                    })
                    continue
                
                is_valid, error_msg = self.validate_query_params(
                    channel=channel,
                    table=table
                )
                if not is_valid:
                    results.append({
                        'success': False,
                        'error': f'第{i + 1}个查询: {error_msg}',
                        'index': i
                    })
                    continue
                
                # 构建并执行查询
                builder = OCPCQueryBuilder(table)
                sql, params = (builder
                              .add_channel_filter(channel)
                              .add_time_range_filter(start_time, end_time)
                              .set_order(order)
                              .build())
                
                # 为OCPC查询使用专门的数据库环境
                ocpc_env = f"{env}_ocpc" if not env.endswith('_ocpc') else env
                
                data_result = self.db_manager.execute_query(sql, params, ocpc_env)
                
                results.append({
                    'success': True,
                    'table': table,
                    'channel': channel,
                    'start_time': start_time,
                    'end_time': end_time,
                    'order': order,
                    'count': len(data_result),
                    'data': data_result,
                    'index': i
                })
                
            except Exception as e:
                logger.error(f"批量查询第{i + 1}项失败: {str(e)}", exc_info=True)
                results.append({
                    'success': False,
                    'error': f'第{i + 1}个查询执行失败: {str(e)}',
                    'index': i
                })
        
        return results
