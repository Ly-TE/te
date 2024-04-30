'''
接口的关键字驱动类：封装常用的接口测试方法

'''

import requests
from conf import read_conf


class Apikeys:
    def do_get(self, headers=None, params=None, path=None, **kwargs):
        """
        发送 GET 请求

        Args:
            headers (dict): 请求头信息，默认为 None
            params (dict): 请求参数，默认为 None
            path (str): URL 路径，默认为 None
            **kwargs: 其他关键字参数

        Returns:
            requests.models.Response: 请求响应对象
        """
        url = self.set_url(path)
        headers = self.set_headers(headers)
        return requests.get(url=url, headers=headers, params=params, **kwargs)

    def do_post(self, headers=None, data=None, path=None, is_json=True, **kwargs):
        """
        发送 post 请求
        如果需要传递json格式的内容，需要二次参数化处理

        Args:
            headers (dict): 请求头信息，默认为 None
            data (dict): 请求数据，默认为 None
            path (str): URL 路径，默认为 None
            is_json (bool): 是否以 JSON 格式发送数据，默认为 True
            **kwargs: 其他关键字参数

        Returns:
            requests.models.Response: 请求响应对象
        """
        url = self.set_url(path)
        headers = self.set_headers(headers)
        # 判断是否传入json格式
        if is_json:
            rep = requests.post(url=url, headers=headers, json=data, **kwargs)
        else:
            rep = requests.post(url=url, headers=headers, data=data, **kwargs)
        return rep

    def set_url(self, path=None):
        """
        拼接 URL

        Args:
            path (str): URL 路径，默认为 None

        Returns:
            str: 拼接后的 URL
        """
        url = read_conf.read('servers', 'Dev')  # 假设 'servers' 是配置文件中的部分，'Dev' 是选项
        if path:
            url = url + path
        return url

    def set_headers(self, headers=None):
        """
        拼接请求头信息

        Args:
            headers (dict): 额外的请求头信息，默认为 None

        Returns:
            dict: 拼接后的请求头信息
        """
        # 定义通用的基础头信息：简化请求时的参数设置和定义，简化测试用例的数据内容
        base_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/125.0.0.0 Safari/537.36 '
        }
        if headers:
            base_headers.update(headers)
        return base_headers


