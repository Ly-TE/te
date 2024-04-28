import time
from appium import webdriver

# 实例化驱动对象
desired_caps = dict()
desired_caps['platformName'] = 'Android'
desired_caps['platformVersion'] = '14'
desired_caps['deviceName'] = '10AD132ER600206'
desired_caps['appPackage'] = 'com.nn.accelerator.box'
desired_caps['appActivity'] = '.activity.MainActivity'

print("Creating driver...")
driver = webdriver.Remote("http://localhost:4723/wd/hub", desired_caps)

try:
    # 执行测试步骤
    time.sleep(3)
finally:
    # 关闭驱动对象
    try:
        print("Quitting driver...")
        if driver is not None:
            driver.quit()
    except Exception as e:
        print("An error occurred while quitting the driver:", e)
