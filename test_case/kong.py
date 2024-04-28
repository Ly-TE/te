# 读取文件内容
file_path = "D:/1.txt"
with open(file_path, 'r+') as file:
    file_content = file.read()

    # 去除空格
    file_content_without_spaces = file_content.replace(" ", "")

    # 将光标移动到文件开头，以便覆盖原有内容
    file.seek(0)

    # 写入处理后的内容覆盖原有内容
    file.write(file_content_without_spaces)

# 输出处理后的内容
print("处理后的内容已覆盖原文件。")

# 暂停等待用户输入
input("按下 Enter 键以退出程序...")
