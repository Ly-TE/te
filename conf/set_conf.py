import configparser
import pathlib

# 定义 conf.ini 的文件路径
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

# 写入配置信息
def write(section, option, value):
    conf = configparser.ConfigParser()
    conf.read(file)

    if not conf.has_section(section):
        conf.add_section(section)

    conf.set(section, option, value)

    # 使用 'w' 模式重新写入配置文件
    with open(file, 'w') as f:
        conf.write(f)

# 示例读取配置信息
try:
    server = read('servers', 'Dev')
    print("Server:", server)
except (FileNotFoundError, KeyError) as e:
    print("错误:", e)
