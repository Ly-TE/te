import requests

url = 'https://webapi.leigod.com/api/auth/login'
data = {
  "os_type": 4,
  "password": "f02d49289d80a01a7fa36aa9281e6904",
  "mobile_num": "13997505254",
  "src_channel": "guanwang",
  "sem_ad_img_url": {
    "url": "",
    "btn_yrl": ""
  },
  "country_code": 86,
  "username": "13997505254",
  "lang": "zh_CN",
  "region_code": 1,
  "account_token": None
}

rep = requests.post(url=url,json=data)
print(rep.text)
