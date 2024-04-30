'''
获取配置文件中的相关信息

'''

import configparser
import pathlib

# 定义conf.ini的文件路径
file = pathlib.Path(__file__).parents[0].resolve() / 'conf.ini'


# 读取配置信息
def read(section, option):
    if not file.exists():
        raise FileNotFoundError("配置文件不存在！")

    conf = configparser.ConfigParser()
    conf.read(file)

    if section not in conf:
        raise KeyError(f"找不到配置文件中的 '{section}' 部分！")

    if option not in conf[section]:
        raise KeyError(f"找不到 '{section}' 部分中的 '{option}' 选项！")

    return conf.get(section, option)


print(read('servers', 'Dev'))
