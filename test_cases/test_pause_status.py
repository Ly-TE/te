from commons.requests_utils import RequestUtils
from test_cases.test_client_login import TestApi
import pytest


class TestApi2:
    @pytest.mark.smoke
    def test_pause_status(self):
        api = TestApi()
        api.test_client_login()
        urls = 'http://vf-api2.nn.com/client/pause/status?client_version = 10.1.8.8&inline_version = 1721726589482&area_code = HB&os_type = 0&region_code = 1'
        datas = {
            "account_token": api.account_token,
            "is_off_rc4": "off"
        }
        res = RequestUtils().send_all_request(method='post', url=urls, params=datas)


# if __name__ == '__main__':
#     TestApi2().test_pause_status()