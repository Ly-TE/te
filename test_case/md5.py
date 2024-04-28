import os
import hashlib
import msvcrt

def calculate_folder_hash(folder_path):
    md5_hash = hashlib.md5()

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    md5_hash.update(chunk)

    return md5_hash.hexdigest()

folder_path = input("请输入文件夹路径：")
folder_hash = calculate_folder_hash(folder_path)
print(f"MD5 hash of folder '{folder_path}': {folder_hash}")
# 等待用户按下任意键
print("按下任意键继续...")
msvcrt.getch()  # 等待用户按下任意键