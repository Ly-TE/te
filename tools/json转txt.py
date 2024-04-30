import json

# 定义一个 JSON 对象
json_data = {
  "src_channel": "leigodPC",
  "android_url": "https://dfs01.nn.com/v2/default/1713240122/1528/leigodPC-release-1.6.1-514-20240415173054_dbb5b022_enc_sign.apk",
  "ios_url": "https://apps.apple.com/cn/app/id1613506145"
}

# 使用 json.dumps() 将 JSON 对象转换为字符串，并指定格式化参数
formatted_text = json.dumps(json_data, indent=4, ensure_ascii=False)

# 打印格式化后的文本
print(formatted_text)
