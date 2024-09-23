from DrissionPage import ChromiumPage, ChromiumOptions
import time

path = r"E:\NN\nn.exe"
co = ChromiumOptions().set_browser_path(path)
p = ChromiumPage(co)

# input('回车开始')

time.sleep(10)  # 增加等待时间，等待 10 秒

try:
    element = p.ele('#mainContainer > section > aside > div > div.relative.no-drag.nn-tooltip__trigger.nn-tooltip__trigger > img')
    element.click()
except Exception as e:
    print(f"操作时发生错误: {e}")

p.close()