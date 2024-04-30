import unittest
import json
from api_keys.keys import Apikeys
from ddt import ddt, file_data
from urllib.parse import unquote  # 添加导入语句


@ddt
class TestApi(unittest.TestCase):
    @file_data('../test_data/login.yaml')
    def test_login(self, **kwargs):
        path = kwargs.get('path')
        data = kwargs.get('data')

        api = Apikeys()

        rep = api.do_post(path=path, data=data)

        # 将返回结果解析为JSON对象
        response_json = json.loads(rep.text)

        # 解码其中的文本部分
        decoded_text = json.dumps(response_json, ensure_ascii=False)
        print(decoded_text)


if __name__ == '__main__':
    unittest.main()
