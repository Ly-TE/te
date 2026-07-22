import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from DB.database import db_manager

# 获取所有表名
result = db_manager.execute_query("SHOW TABLES", env='testing')
all_tables = [row['Tables_in_leigod_config'] for row in result]

print("查找可能的OCPC相关表名:")
ocpc_tables = []
for table in all_tables:
    if any(keyword in table.lower() for keyword in ['ocpc', 'mapping', 'log']):
        print(f"  - {table}")
        ocpc_tables.append(table)

print(f"\n总共找到 {len(ocpc_tables)} 个可能相关的表")

# 如果没有找到，列出一些可能的表
if not ocpc_tables:
    print("\n没有找到OCPC相关表，列出一些可能相关的表:")
    sample_tables = all_tables[:20]  #显示前20个表
    for table in sample_tables:
        print(f"  - {table}")