'''
用例的执行
'''

import unittest
from .api_keys.keys import ApiKeys
from ddt import ddt, file_data


@ddt
class TestApi(unittest.TestCase):
    @file_data('../test_data/login.yaml')
    def test_01_login(self, **kwargs):
        # 从测试数据中获取路径和数据
        path = kwargs.get('path')
        data = kwargs.get('data')

        # 实例化 ApiKeys 类
        api = ApiKeys()

        # 执行登录操作
        rep = api.do_post(path=path, data=data)

        # 打印响应文本内容
        print(rep.text)


if __name__ == '__main__':
    unittest.main()
