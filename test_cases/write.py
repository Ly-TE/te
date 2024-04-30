import unittest
from api_keys.keys import Apikeys
from ddt import ddt, file_data
from conf import set_conf

@ddt
class TestApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # 设置测试类共享的 API 实例
        cls.api = Apikeys()

    @file_data('../test_data/login.yaml')
    def test_01_login(self, **kwargs):  # 接收参数 kwargs
        # 在每个测试方法执行前发送登录请求，并设置账户令牌
        rep = self.api.do_post(**kwargs)
        account_token = set_conf.read('headers', 'account_token')  # 从配置文件读取账户令牌
        print(account_token)  # 打印账户令牌，用于调试

if __name__ == '__main__':
    unittest.main()
