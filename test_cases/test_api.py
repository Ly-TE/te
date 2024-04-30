import unittest
import json
from api_keys.keys import Apikeys
from ddt import ddt, file_data


@ddt
class TestApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.api = Apikeys()
        cls.account_token = None

    @file_data('../test_data/login.yaml')
    def test_01_login(self, **kwargs):
        rep = self.api.do_post(**kwargs)

        # 将返回结果解析为JSON对象
        response_json = json.loads(rep.text)

        # 解码其中的文本部分
        decoded_text = json.dumps(response_json, ensure_ascii=False)
        print(decoded_text)
        self.account_token = response_json['data']['login_info']['account_token']

        print(self.account_token)

    @file_data('../test_data/bannerlist.yaml')
    def test_02_bannerlist(self, **kwargs):
        rep = self.api.do_get(**kwargs)
        response_json = json.loads(rep.text)
        decoded_text = json.dumps(response_json, ensure_ascii=False)
        print(decoded_text)


if __name__ == '__main__':
    unittest.main()
