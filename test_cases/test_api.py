import unittest
import json
from api_keys.keys import Apikeys
from ddt import ddt, file_data


@ddt
class TestApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # 设置测试类共享的 API 实例和账户令牌
        cls.api = Apikeys()
        cls.account_token = None

    @file_data('../test_data/login.yaml')
    def test_01_login(self, **kwargs):
        # 发送登录请求
        rep = self.api.do_post(**kwargs)

        # 将返回结果解析为 JSON 对象
        response_json = json.loads(rep.text)

        # 断言登录是否成功
        self.assertEqual(rep.status_code, 200)
        self.assertTrue('data' in response_json)
        self.assertTrue('login_info' in response_json['data'])
        self.assertTrue('account_token' in response_json['data']['login_info'])
        # 全局变量形式实现数据传递
        # 提取 account_token
        self.account_token = response_json['data']['login_info']['account_token']
        print("Account Token:", self.account_token)

    @file_data('../test_data/bannerlist.yaml')
    def test_02_bannerlist(self, **kwargs):
        # 在请求头中添加账户令牌
        kwargs['headers'] = {'account_token': self.account_token}
        rep = self.api.do_get(**kwargs)
        response_json = json.loads(rep.text)

        # 断言获取 banner 列表是否成功
        self.assertEqual(rep.status_code, 200)
        self.assertTrue('data' in response_json)
        self.assertTrue(isinstance(response_json['data'], list))
        self.assertTrue(len(response_json['data']) > 0)
        self.assertTrue('title' in response_json['data'][0])

        # 打印返回的 JSON 内容，用于调试
        decoded_text = json.dumps(response_json, ensure_ascii=False)
        print(decoded_text)


if __name__ == '__main__':
    unittest.main()
