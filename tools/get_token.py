import requests
import json

# 获取用户输入的手机号并进行简单验证
phone_number = input("请输入手机号码：")
if not phone_number.isdigit() or len(phone_number)!= 11:
    print("输入的手机号码格式不正确。")
    exit()

# 配置第一个接口 URL 和一些常量
first_api_url = 'https://test-opapi.xxghh.biz/u-mobile/registerLogin'

# 第一个接口的请求数据
data = {
    "countryCode": 86,
    "smsCode": "8888",
    "smsCodeKey": "",
    "telNum": phone_number
}

headers = {
    'Content-Type': 'application/json; charset=UTF-8',
    'adan': 'oaid=FABFA4EEB7AC4C89A5FFB4243B61848C37e90cb05f18c4331645758088de800a',
    'anonymousId': '2d91ac85beeb2307a8c4f99d71dbecf29',
    'appId': 'nnMobile_d0k3duup',
    'appName': 'leigod_accelerator',
    'busiType': 'nn_aksjfdasoifnkls',
    'deviceId': 'ffffffff-ee90-2013-0000-000065c837d7',
    'latitude': '0.0',
    'longitude': '0.0',
    'mobileBrand': 'OnePlus',
    'mobileModel': 'NE2210',
    'osVersion': '14',
    'platform': '2',
    'registerCanal': 'common',
    'reqChannel': '2',
    'sign': '',
    'signType': '1',
    'timeStamp': '1730356157906',
    'token': '',
    'version': '526'
}

def send_request(url, headers, data):
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            return response.json()
        else:
            print(f"请求失败，状态码：{response.status_code}，错误信息：{response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"请求发生异常：{e}")
        return None

# 发送第一个 POST 请求
first_response = send_request(first_api_url, headers, data)

if first_response:
    # 提取第一个接口返回的 token
    token = first_response.get('retData', {}).get('token', '')
    token_result = {
        "app_id": first_response.get('retData', {}).get('app_id', ''),
        "ts": first_response.get('retData', {}).get('ts', ''),
        "sign": first_response.get('retData', {}).get('sign', ''),
        "user_id": first_response.get('retData', {}).get('userId', ''),
        "src_channel": first_response.get('retData', {}).get('src_channel', ''),
        "country_code": first_response.get('retData', {}).get('countryCode', ''),
        "phone": phone_number,
        "nn_number": first_response.get('retData', {}).get('nnNumber', '')
    }
    print(token_result)
    # 配置下一个接口 URL 和请求头
    next_api_url = 'http://vf-webapi.leigod.com/passport/web/token'
    next_headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'adan': 'oaid=FABFA4EEB7AC4C89A5FFB4243B61848C37e90cb05f18c4331645758088de800a',
        'anonymousId': '2d91ac85beeb2307a8c4f99d71dbecf29',
        'appId': 'nnMobile_d0k3duup',
        'appName': 'leigod_accelerator',
        'busiType': 'nn_aksjfdasoifnkls',
        'deviceId': 'ffffffff-ee90-2013-0000-000065c837d7',
        'latitude': '0.0',
        'longitude': '0.0',
        'mobileBrand': 'OnePlus',
        'mobileModel': 'NE2210',
        'osVersion': '14',
        'platform': '2',
        'registerCanal': 'common',
        'reqChannel': '2',
        'sign': '',
        'signType': '1',
        'timeStamp': '1730356158274',
        'token': token,
        'version': '526'
    }
    # 发送下一个接口请求
    next_response = send_request(next_api_url, next_headers, json.dumps(token_result))
    if next_response:
        print(next_response)
    else:
        print("下一个接口请求失败。")
else:
    print("第一个接口请求失败。")