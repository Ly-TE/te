import requests
import json

url = "http://twserver.leigod.com/users"

# 请求参数
data = {
    "access_token": "dxzhze662e7zy20sac7zk4ql50s60y",
    "refresh_token": "qd4a7148ziif0v9yqr4paurdgwld5o5bxnix39jru9f3r37jwg",
    "twitch_id": "1003385131",
    "twitch_name": "pizewing"
}

# 发送POST请求
response = requests.post(url, json=data)

# 检查响应状态码
if response.status_code == 200:
    # 获取返回结果
    result = response.json()
    print(result)
else:
    print("请求失败，状态码：", response.status_code)
