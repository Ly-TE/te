import threading
import requests
import json

def send_post_request(payload):
    url = 'http://vf-webapi2.leigod.com/api/invite/user/receive?client_version=10.1.4.2&inline_version=1701227418904&os_type=0'
    headers = {'Content-Type': 'application/json'}

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response_text = response.text.replace('{', '{\n').replace('}', '\n}').replace(',', ',\n')
    print(response_text)

# 创建多个线程并发发起请求
num_threads =1
threads = []

# 待发送的参数
payload = {
    "activity_id": 10036,
    "account_token": "XFDtYr7SNzV8VYcp4XOnUMM1WcqP93YvCz8ABs55UtHXNW13dj285pQDalxbRHiR",
    "task_id": 38
}

for _ in range(num_threads):
    thread = threading.Thread(target=send_post_request, args=(payload,))
    threads.append(thread)
    thread.start()

# 等待所有线程结束
for thread in threads:
    thread.join()
