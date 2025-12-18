import requests
import json
import pytest


class TestLoginAPI:
    """登录接口测试类"""

    base_url = "https://vf-thorfastapi.leigod.com/client/login/code"
    headers = {'Content-Type': 'application/json'}

    def make_request(self, params):
        """统一请求方法"""
        try:
            # 移除test_case_name参数，它只用于显示
            request_params = {k: v for k, v in params.items() if k != 'test_case_name'}

            response = requests.request(
                "POST",
                self.base_url,
                params=request_params,
                headers=self.headers,
                timeout=30
            )
            return response
        except Exception as e:
            print(f"请求异常: {str(e)}")
            return None

    # ==================== 一、正向测试用例 ====================

    def test_positive_01_only_required_fields(self):
        """TC1-正向-仅传必要字段"""
        params = {
            'test_case_name': 'TC1-正向-仅传必要字段',
            'client_version': '2.0.2.4',
            'country_code': '86',
            'mobile_num': '17764000760',
            'os_type': '0',
            'smscode': '8888',
            'smscode_key': 'FV0qixVilXu33NyUYRNp54dWRnD8oFhhEf49JdgVXN9Us95NKDaB20o5unF8abTN',
            'src_channel': 'guanwang'
        }
        response = self.make_request(params)
        print(f"测试用例: {params['test_case_name']}")
        print(f"状态码: {response.status_code if response else '无响应'}")
        assert response is not None
        assert response.status_code == 200

    def test_positive_02_all_fields(self):
        """TC2-正向-完整参数"""
        params = {
            'test_case_name': 'TC2-正向-完整参数',
            'client_version': '2.0.2.4',
            'country_code': '86',
            'device_info': 'device_info',
            'hardware_id': '15ae58b1-ab6b-4ad9-8429-7f29d8a99350',
            'mobile_num': '17764000760',
            'os_type': '0',
            'smscode': '8888',
            'smscode_key': 'FV0qixVilXu33NyUYRNp54dWRnD8oFhhEf49JdgVXN9Us95NKDaB20o5unF8abTN',
            'src_channel': 'guanwang',
            'is_off_rc4': 'off',
            'locale': 'en'
        }
        response = self.make_request(params)
        print(f"测试用例: {params['test_case_name']}")
        print(f"状态码: {response.status_code if response else '无响应'}")
        assert response is not None
        assert response.status_code == 200

    # ==================== 二、负向测试用例 ====================

    def test_negative_01_missing_required_smscode_key(self):
        """TC3-负向-缺失必填字段smscode_key"""
        params = {
            'test_case_name': 'TC3-负向-缺失smscode_key',
            'client_version': '2.0.2.4',
            'country_code': '86',
            'mobile_num': '17764000766',
            'os_type': '0',
            'smscode': '8888',
            'src_channel': 'guanwang'
        }
        response = self.make_request(params)
        print(f"测试用例: {params['test_case_name']}")
        print(f"状态码: {response.status_code if response else '无响应'}")
        assert response is not None

    def test_negative_02_invalid_mobile_num_format(self):
        """TC4-负向-手机号格式错误"""
        params = {
            'test_case_name': 'TC4-负向-手机号格式错误',
            'client_version': '2.0.2.4',
            'country_code': '86',
            'mobile_num': '12345',  # 格式错误的手机号
            'os_type': '0',
            'smscode': '8888',
            'smscode_key': 'FV0qixVilXu33NyUYRNp54dWRnD8oFhhEf49JdgVXN9Us95NKDaB20o5unF8abTN',
            'src_channel': 'guanwang'
        }
        response = self.make_request(params)
        print(f"测试用例: {params['test_case_name']}")
        print(f"状态码: {response.status_code if response else '无响应'}")
        assert response is not None

选择生成的用例类型