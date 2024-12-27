import requests
import json

url = "https://opapi1.xxghh.biz/speed/console/game/label/repo"
payload = {"platform": "2"}
headers = {
    "reqChannel": "2",
    "Content-Type": "application/json"  # 添加Content-Type请求头，指定数据格式为JSON
}
response = requests.request("POST", url, headers=headers, data=json.dumps(payload))  # 将payload转换为JSON字符串格式发送
print(response.json())