#!/usr/bin/env python
"""
使用信息模式直接查询表和列信息 - 修复版
"""
import pymysql
from pymysql.cursors import DictCursor

config = {
    'host': '123.60.66.91',
    'port': 33506,
    'user': 'leigod_pre_w',
    'password': 'VgLaQcyoheXpsx',
    'charset': 'utf8mb4'
}


def query_information_schema():
    """查询信息模式"""
    try:
        conn = pymysql.connect(**config, cursorclass=DictCursor)  # 添加 cursorclass
        cursor = conn.cursor()

        print("🔍 查询信息模式")
        print("=" * 60)

        # 1. 查找包含 ocpc 的表
        query = """
        SELECT 
            TABLE_SCHEMA as '数据库',
            TABLE_NAME as '表名',
            TABLE_ROWS as '行数',
            CREATE_TIME as '创建时间'
        FROM information_schema.TABLES 
        WHERE TABLE_NAME LIKE '%ocpc%'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
        """

        cursor.execute(query)
        ocpc_tables = cursor.fetchall()

        print(f"\n📊 找到 {len(ocpc_tables)} 个包含 'ocpc' 的表:")
        for table in ocpc_tables:
            print(f"   {table['数据库']}.{table['表名']} (行数: {table['行数'] or 0})")

        # 2. 查找包含 mapping 的表
        query = """
        SELECT 
            TABLE_SCHEMA as '数据库',
            TABLE_NAME as '表名'
        FROM information_schema.TABLES 
        WHERE TABLE_NAME LIKE '%mapping%'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
        """

        cursor.execute(query)
        mapping_tables = cursor.fetchall()

        print(f"\n📊 找到 {len(mapping_tables)} 个包含 'mapping' 的表:")
        for table in mapping_tables[:10]:
            print(f"   {table['数据库']}.{table['表名']}")

        if len(mapping_tables) > 10:
            print(f"   ... 还有 {len(mapping_tables) - 10} 个表")

        # 3. 查找包含 channel 字段的表
        query = """
        SELECT DISTINCT
            TABLE_SCHEMA as '数据库',
            TABLE_NAME as '表名',
            COLUMN_NAME as '字段名'
        FROM information_schema.COLUMNS 
        WHERE COLUMN_NAME LIKE '%channel%'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
        """

        cursor.execute(query)
        channel_tables = cursor.fetchall()

        print(f"\n📊 找到 {len(channel_tables)} 个包含 'channel' 字段的表:")
        for table in channel_tables[:15]:
            print(f"   {table['数据库']}.{table['表名']} ({table['字段名']})")

        conn.close()

    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    query_information_schema()