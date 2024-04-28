from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep

# 设置ChromeDriver的路径
chrome_driver_path = r'C:\Users\admin\AppData\Local\Google\Chrome\Application\chromedriver.exe'

# 创建Chrome WebDriver
service = Service(chrome_driver_path)
wd = webdriver.Chrome(service=service)

# 打开网页
wd.get("https://example.com")

try:
    # 使用CSS选择器定位悬停的元素
    hover_element = wd.find_element(By.CSS_SELECTOR, '#example_element')

    # 创建ActionChains对象
    actions = ActionChains(wd)

    # 将鼠标悬停在元素上
    actions.move_to_element(hover_element).perform()

    # 等待一段时间，以便可以看到效果
    sleep(5)

finally:
    # 手动关闭 WebDriver
    wd.quit()
