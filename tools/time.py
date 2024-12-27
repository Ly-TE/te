import datetime

while True:
    # 获取当前时间
    current_time = datetime.datetime.now()
    print(current_time)

    # 输入秒数
    seconds_to_add = int(input("请输入要增加的秒数："))

    # 将当前时间转换为总秒数
    current_total_seconds = current_time.hour * 3600 + current_time.minute * 60 + current_time.second

    # 加上输入的秒数
    new_total_seconds = current_total_seconds + seconds_to_add

    # 计算新的天数、小时、分钟和秒
    days, remaining_seconds = divmod(new_total_seconds, 86400)
    new_hour = remaining_seconds // 3600
    remaining_seconds %= 3600
    new_minute = remaining_seconds // 60
    new_second = remaining_seconds % 60

    # 更新日期
    new_date = current_time + datetime.timedelta(days=days)

    # 创建新的时间对象
    new_time = datetime.datetime(new_date.year, new_date.month, new_date.day, new_hour, new_minute, new_second)

    print(f"加上 {seconds_to_add} 秒后的时间是：{new_time.strftime('%Y-%m-%d %H:%M:%S')}")

    continue_choice = input("是否继续？（y/n）")
    if continue_choice.lower()!= 'y':
        break