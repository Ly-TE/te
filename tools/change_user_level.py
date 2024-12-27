import tkinter as tk
from tkinter import messagebox
import pymysql
import redis
from redis.exceptions import RedisError
import logging

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

host = '172.31.4.15'
port = 33506
user = 'nn_busi'
password = 'alBIZ3LmPBfI6kYsR9mp'
db = 'nn_speed'

# Redis连接信息
redis_host = '172.31.16.3'
redis_port = 32187
redis_password = 'LbCn_jMT8NGp8x2NyL9'
# 用户等级描述字典
level_descriptions = {
    9: "当日注册新用户-新-A类",
    10: "未付费用户-新-A类",
    11: "临期/过期用户-新-A类",
    12: "普通身份-当日下单用户-新-A类",
    13: "新用户身份-当日下单用户-新-A类",
    14: "未付费身份-当日下单用户-新-A类",
    15: "临期/过期身份-当日下单用户-新-A类",

    39: "当日注册新用户-新-B类",
    40: "未付费用户-新-B类",
    41: "临期/过期用户-新-B类",
    42: "普通身份-当日下单用户-新-B类",
    43: "新用户身份-当日下单用户-新-B类",
    44: "未付费身份-当日下单用户-新-B类",
    45: "临期/过期身份-当日下单用户-新-B类",

    99: "普通用户"
}


def query_and_update_user_level():
    try:
        # 建立数据库连接
        conn = pymysql.connect(host=host, port=port, user=user, password=password, db=db)
        cursor = conn.cursor()

        # 连接Redis
        r = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password)

        # 获取用户输入的手机号码
        tel_num = entry_tel_num.get()

        # 打印所有等级描述
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "所有用户等级描述：\n")
        for level, description in level_descriptions.items():
            result_text.insert(tk.END, f"等级 {level}: {description}\n")

        # 查询用户等级和user_id
        query_sql = f"SELECT level, user_id FROM `leigod_app_activity`.`t_app_user_level` WHERE `tel_num` = '{tel_num}'"
        cursor.execute(query_sql)
        result = cursor.fetchone()
        if result:
            level = result[0]
            user_id = result[1]
            description = level_descriptions.get(level, '未知等级')
            result_text.insert(tk.END, f"\n【用户等级查询结果】\n")
            result_text.insert(tk.END, f"手机号码：{tel_num}\n")
            result_text.insert(tk.END, f"当前等级：{level}\n")
            result_text.insert(tk.END, f"等级描述：{description}\n")
            result_text.insert(tk.END, f"用户 ID：{user_id}\n")
        else:
            result_text.insert(tk.END, f"\n该手机号不存在，请检查输入。\n")

        # 获取用户输入的新等级并更新用户等级
        new_level_str = entry_new_level.get()
        if new_level_str:
            try:
                new_level = int(new_level_str)
                if new_level not in level_descriptions:
                    result_text.insert(tk.END, f"\n输入的等级数字不合法。\n")
                    return
                update_sql = f"UPDATE `leigod_app_activity`.`t_app_user_level` SET level={new_level} WHERE tel_num='{tel_num}'"
                cursor.execute(update_sql)
                conn.commit()
                new_description = level_descriptions.get(new_level, '未知等级')
                result_text.insert(tk.END, f"\n【用户等级更新结果】\n")
                result_text.insert(tk.END, f"手机号码：{tel_num}\n")
                result_text.insert(tk.END, f"更新后的等级：{new_level}\n")
                result_text.insert(tk.END, f"等级描述：{new_description}\n")
                result_text.insert(tk.END, f"用户 ID：{user_id}\n")

                # 删除Redis中的相关缓存，添加user_id到键名
                cache_key = f'user_level_{user_id}'
                try:
                    r.delete(cache_key)
                except Exception as e:
                    result_text.insert(tk.END, f"删除用户缓存键 {cache_key} 失败：{e}\n")
                    logging.error(f"删除用户缓存键 {cache_key} 失败：{e}")

                # 删除DB0中的特定键
                r.select(0)
                try:
                    key_to_delete_1 = f'app:user:level:info:{user_id}'
                    # result_text.insert(tk.END, f"尝试删除键：{key_to_delete_1}\n")
                    r.delete(key_to_delete_1)
                except RedisError as e:
                    result_text.insert(tk.END, f"删除键 '{key_to_delete_1}' 失败，错误原因：{e}\n")
                    logging.error(f"删除键 '{key_to_delete_1}' 失败，错误原因：{e}")

                try:
                    key_to_delete_2 = f'app:user:assist:level:info:{user_id}'
                    # result_text.insert(tk.END, f"尝试删除键：{key_to_delete_2}\n")
                    r.delete(key_to_delete_2)
                except RedisError as e:
                    result_text.insert(tk.END, f"删除键 '{key_to_delete_2}' 失败，错误原因：{e}\n")
                    logging.error(f"删除键 '{key_to_delete_2}' 失败，错误原因：{e}")
                except Exception as e:
                    result_text.insert(tk.END, f"删除键 '{key_to_delete_2}' 失败：{e}\n")
                    logging.error(f"删除键 '{key_to_delete_2}' 失败：{e}")
            except ValueError:
                result_text.insert(tk.END, f"\n输入的不是有效的数字。\n")
                logging.error("输入的不是有效的数字。")
            except Exception as e:
                conn.rollback()
                result_text.insert(tk.END, f"\n更新用户等级时出现错误：{e}\n")
                logging.error(f"更新用户等级时出现错误：{e}")
        else:
            result_text.insert(tk.END, f"\n请输入新的用户等级数字。\n")

        cursor.close()
        conn.close()
        r.connection_pool.disconnect()
    except Exception as e:
        result_text.insert(tk.END, f"\n连接数据库或Redis时出现错误：{e}\n")
        logging.error(f"连接数据库或Redis时出现错误：{e}")

    # 将焦点设置回手机号码输入框
    entry_tel_num.focus_set()

def on_enter_tel_num(event):
    query_and_update_user_level()


def on_enter_new_level(event):
    query_and_update_user_level()
    # 将焦点设置回手机号码输入框
    entry_tel_num.focus_set()


# 创建主窗口
root = tk.Tk()
root.title("测试环境用户等级查询与更新工具")
# icon_path = r"C:\Users\admin\Desktop\favicon.ico"
# root.iconbitmap(icon_path)

# 创建输入手机号码的标签和输入框
label_tel_num = tk.Label(root, text="请输入用户手机号码：")
label_tel_num.pack()
entry_tel_num = tk.Entry(root)
entry_tel_num.pack()
entry_tel_num.focus_set()  # 设置焦点到手机号码输入框
entry_tel_num.bind('<Return>', on_enter_tel_num)

# 创建输入新等级的标签和输入框
label_new_level = tk.Label(root, text="请输入新的用户等级数字：")
label_new_level.pack()
entry_new_level = tk.Entry(root)
entry_new_level.pack()
entry_new_level.focus_set()  # 设置焦点到新等级输入框
entry_new_level.bind('<Return>', on_enter_new_level)

# 创建显示结果的文本框和垂直滚动条
result_text = tk.Text(root, height=30, width=80)
scrollbar = tk.Scrollbar(root, command=result_text.yview)
result_text.config(yscrollcommand=scrollbar.set)
result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# 创建查询和更新按钮
button_query_update = tk.Button(root, text="查询并更新", command=query_and_update_user_level)
button_query_update.pack()

# 运行主窗口的事件循环
root.mainloop()