import requests
import json

url = "https://twserver.leigod.com/status/1010732775"

# 发送GET请求
response = requests.get(url)

# 检查响应状态码
if response.status_code == 200:
    # 获取返回结果中的data字段
    data = response.json().get("data")

    if data is not None:
        # 检查data字段是否为空
        if data is not None:
            try:
                # 将data字段转换为JSON格式
                data_json = json.loads(data)

                # 使用json.dumps函数对JSON进行美化输出
                pretty_json = json.dumps(data_json, indent=4, ensure_ascii=False)

                # 打印美化后的JSON
                print(pretty_json)

            except json.JSONDecodeError as e:
                print("JSON解析错误:", str(e))
        else:
            print("返回结果中的data字段为空")
    else:
        print("用户不存在")
else:
    print("请求失败，状态码：", response.status_code)
