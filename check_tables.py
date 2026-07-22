import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from DB.database import db_manager

#检查所有包含mapping或log的表
result = db_manager.execute_query("SHOW TABLES", env='testing')
print("所有表名:")
for row in result:
    table_name = row['Tables_in_leigod_config']
    if 'mapping' in table_name.lower() or 'log' in table_name.lower() or 'ocpc' in table_name.lower():
        print(f"  - {table_name}")

#检查具体的表是否存在
print("\n检查特定表:")
tables_to_check = ['tbl_ocpc_mapping', 'tbl_ocpc_log', 'ocpc_mapping', 'ocpc_log']
for table in tables_to_check:
    try:
        result = db_manager.execute_query(f"SELECT COUNT(*) as count FROM `{table}` LIMIT 1", env='testing')
        print(f"✓表 {table}存在")
    except Exception as e:
        print(f"✗ 表 {table} 不存在: {str(e)}")