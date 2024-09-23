import random
import string

filename = 'large_file.txt'
file_size = 1 * 1024 * 1024 * 1024 # 文件大小为5GB

with open(filename, 'w') as f:
    f.write(''.join(random.choices(string.ascii_uppercase + string.digits, k=1024)) * (file_size//1024))
