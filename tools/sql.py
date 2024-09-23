import pymysql

# 数据库连接信息
host = '172.31.4.15'
port = 33506
user = 'nn_busi'
password = 'alBIZ3LmPBfI6kYsR9mp'
db = 'nn_speed'

# 建立数据库连接
conn = pymysql.connect(host=host, port=port, user=user, password=password, db=db)
cursor = conn.cursor()

count = 41999  # 初始值

for _ in range(35000):
    sql_statement = f"""
    INSERT INTO `nn_speed`.`game_white_info` ( `game_key`, `rule_type`, `rule_content`, `order_num`, `create_by`, `create_time`, `update_by`, `update_time`, `game_i_d`, `version`, `area`, `node`, `executor`, `creat_time`, `result`, `type`, `ua`, `url`, `game_base_id`, `area_type`, `url_type`, `name`, `platform`, `use_status`, `use_global`) 
    VALUES ( NULL, '2', '{count}', 1, '17362756487', '2020-11-11 17:41:51', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 51328, NULL, NULL, NULL, 1, 1, 1)
    """
    try:
        cursor.execute(sql_statement)
        count += 1  # 每次插入后递增
    except Exception as e:
        print(f"执行第 {_ + 1} 次时出错: {e}")

conn.commit()  # 提交更改
cursor.close()  # 关闭游标
conn.close()  # 关闭连接