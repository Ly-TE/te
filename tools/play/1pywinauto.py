import time
import logging
from pywinauto import Application
import re
import pyscreenshot as ImageGrab

logging.basicConfig(level=logging.DEBUG)

app = Application(backend="uia").start("E:\leigod\leigod_launcher.exe")
logging.info("应用已成功启动")

found = False
loop_count = 0
max_retries = 10
while not found and loop_count < max_retries:
    loop_count += 1
    time.sleep(5)  # 增加等待时间
    try:
        app_dialogs = app.windows()
        for dialog in app_dialogs:
            logging.debug(f"循环 {loop_count}: 当前窗口标题为 {dialog.window_text()}")
            if "雷神加速器" in dialog.window_text():
                found = True
                break
    except Exception as e:
        logging.error(f"查找窗口时出现错误: {e}")

if found:
    app = Application(backend="uia").connect(title="雷神加速器")
    logging.info("已尝试连接到指定标题的窗口")

    # 后续代码...

else:
    logging.error(f"经过 {max_retries} 次尝试后，仍未能找到'雷神加速器'窗口，无法继续执行后续代码。")