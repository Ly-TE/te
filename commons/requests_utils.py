import requests


class RequestUtils:
    sess = requests.session()

    # 统一请求封装
    def send_all_request(self, **kwargs):
        res = RequestUtils.sess.request(**kwargs)
        print(res.text)
        return res
