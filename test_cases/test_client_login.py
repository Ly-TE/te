from commons.requests_utils import RequestUtils
from commons.get_log import logs

class TestApi:
    account_token = ""

    def test_client_login(self):
        urls = "http://vf-api2.nn.com/client/login?client_version = 10.1.8.8&inline_version = 1721726589482&area_code = HB&os_type = 0&region_code = 1"
        datas = {
            "country_code": "86",
            "mobile_num": "13997505254",
            "user_type": 0,
            "password": "f02d49289d80a01a7fa36aa9281e6904",
            "region_code": 1,
            "request_time": "2024 - 09 - 20 11:12:05",
            "src_channel": "guanwang_nn",
            "lang": "zh_CN",
            "os_type": 0,
            "hardware_id": "6fef1d12120b0d510f2a7cd27994e7a6",
            "client_version": "10.1.8.8",
            "is_off_rc4": "off"
        }
        res = RequestUtils().send_all_request(method='post', url=urls, params=datas)
        try:
            json_data = res.json()
            if "data" in json_data:
                self.account_token = json_data["data"]["account_token"]
                logs.info(self.account_token)
            else:
                logs.error("'data' not found in the response")
        except (ValueError, KeyError) as e:
            print(f"Error occurred while getting account_token: {e}")

    def test_pause_status(self):
        urls = 'http://vf-api2.nn.com/client/pause/status?client_version = 10.1.8.8&inline_version = 1721726589482&area_code = HB&os_type = 0&region_code = 1'
        datas = {
            "account_token": self.account_token,
            "is_off_rc4": "off"
        }
        res = RequestUtils().send_all_request(method='post', url=urls, params=datas)


# if __name__ == '__main__':
#     api = TestApi()
#     api.test_client_login()
#     api.test_pause_status()