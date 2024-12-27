import unittest
import logging
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy

# 配置日志记录，方便后续查看测试过程中的详细信息
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

capabilities = {
    "platformName": "Android",
    "automationName": "uiautomator2",
    "deviceName": "Android",
    "appPackage": "com.android.settings",
    "appActivity": ".Settings",
    "language": "en",
    "locale": "US"
}

appium_server_url = "http://localhost:4723"


class TestAppium(unittest.TestCase):
    def setUp(self) -> None:
        """
        初始化测试环境，创建Appium驱动实例并连接到安卓设备及设置应用
        """
        try:
            options = UiAutomator2Options()
            options.load_capabilities(capabilities)
            self.driver = webdriver.Remote(appium_server_url, options=options)
            logging.info("成功连接到Appium服务器并启动设置应用")
        except Exception as e:
            logging.error(f"在初始化驱动时出现错误: {str(e)}")
            raise

    def tearDown(self) -> None:
        """
        清理测试环境，关闭Appium驱动实例
        """
        if self.driver:
            try:
                self.driver.quit()
                logging.info("已成功关闭Appium驱动，释放相关资源")
            except Exception as e:
                logging.error(f"关闭驱动时出现错误: {str(e)}")

    def test_find_battery(self) -> None:
        """
        测试查找并点击安卓设置应用中的电池选项
        """
        try:
            # 优先尝试使用ID定位元素，如果ID定位失败，再尝试使用XPATH定位（可根据实际情况调整定位策略顺序）
            try:
                battery_element = self.driver.find_element(by=AppiumBy.ID,
                                                           value="com.android.settings:id/battery_option_id")  # 替换为实际的ID值
            except:
                logging.warning("使用ID定位电池元素失败，尝试使用XPATH定位")
                battery_element = self.driver.find_element(by=AppiumBy.XPATH, value='//*[@text="Battery"]')

            battery_element.click()
            logging.info("成功点击电池选项")
        except Exception as e:
            logging.error(f"在查找或点击电池选项时出现错误: {str(e)}")
            raise
        


if __name__ == "__main__":
    unittest.main()
