import re
import os
from datetime import datetime


def extract_root_domain(domain):
    """提取根域名（最后两部分）"""
    if not domain or not isinstance(domain, str):
        return None

    domain = domain.strip().lower()

    # 如果是IP地址，直接返回（IP地址不加*）
    ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?$'
    if re.match(ip_pattern, domain):
        return domain.split(':')[0]

    # 移除协议头
    if '://' in domain:
        domain = domain.split('://')[1]

    # 移除端口、路径、查询参数
    domain = domain.split(':')[0].split('/')[0].split('?')[0]

    # 分割域名
    parts = domain.split('.')

    if len(parts) < 2:
        return domain

    # 处理特殊TLD（如.co.uk, .com.cn）
    special_tlds = {'co', 'com', 'net', 'org', 'edu', 'gov', 'ac'}
    country_tlds = {'uk', 'jp', 'cn', 'au', 'tw', 'hk', 'kr', 'us'}

    if len(parts) >= 3:
        tld = parts[-1]
        second_last = parts[-2]
        if tld in country_tlds and second_last in special_tlds:
            return '.'.join(parts[-2:])

    # 返回最后两部分
    return '.'.join(parts[-2:])


# 设置文件路径
base_path = r'D:\WXWork\1688854613328927\Cache\File\2025-12'
files_to_process = ['bilinallwhite.txt', 'leigodallwhite.txt']

# 统计信息
file_stats = []
all_root_domains = set()
total_lines_all = 0
valid_domains_all = 0

print("开始处理文件...\n")

# 处理每个文件
for filename in files_to_process:
    file_path = os.path.join(base_path, filename)

    if not os.path.exists(file_path):
        print(f"文件不存在: {filename}")
        continue

    print(f"处理文件: {filename}")

    file_root_domains = set()
    file_total_lines = 0
    file_valid_domains = 0

    # 尝试不同编码读取
    encodings = ['utf-8', 'gbk', 'latin-1']
    success = False

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                for line in f:
                    file_total_lines += 1
                    line = line.strip()
                    if not line or line.startswith('#') or line.startswith('//'):
                        continue

                    # 提取域名（取第一个字段）
                    parts = line.split()
                    if parts:
                        domain = parts[0]
                        root = extract_root_domain(domain)
                        if root:
                            file_root_domains.add(root)
                            all_root_domains.add(root)
                            file_valid_domains += 1

            success = True
            print(f"  成功读取，编码: {encoding}")
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"  读取失败: {e}")
            continue

    if not success:
        print(f"  无法读取文件 {filename}")
        continue

    # 记录文件统计信息
    file_stats.append({
        'filename': filename,
        'total_lines': file_total_lines,
        'valid_domains': file_valid_domains,
        'unique_roots': len(file_root_domains)
    })

    total_lines_all += file_total_lines
    valid_domains_all += file_valid_domains

    print(f"  文件行数: {file_total_lines}")
    print(f"  有效域名: {file_valid_domains}")
    print(f"  唯一根域名: {len(file_root_domains)}\n")

# 检查是否成功处理了文件
if not file_stats:
    print("没有成功处理任何文件，程序退出。")
    exit()

# 输出总体统计信息
print("=== 总体统计信息 ===")
print(f"处理文件数: {len(file_stats)}")

for stat in file_stats:
    print(f"\n{stat['filename']}:")
    print(f"  文件行数: {stat['total_lines']}")
    print(f"  有效域名: {stat['valid_domains']}")
    print(f"  唯一根域名: {stat['unique_roots']}")

print(f"\n总计:")
print(f"  总行数: {total_lines_all}")
print(f"  总有效域名: {valid_domains_all}")
print(f"  合并后的唯一根域名总数: {len(all_root_domains)}")

# 处理结果：已经有*的就不加，没有的就加*
final_results = []
for root in sorted(all_root_domains):
    if root.startswith('*'):
        # 已经有*，直接使用
        final_results.append(root)
    else:
        # 没有*，加上*
        final_results.append(f"*{root}")

print(f"\n=== 处理后的根域名列表（前20个示例）===")
for i, root in enumerate(final_results[:20], 1):
    print(f"{root}")

if len(final_results) > 20:
    print(f"... 还有 {len(final_results) - 20} 个根域名")

# 保存处理后的结果（带*的）
output_file = os.path.join(base_path, 'wildcard_root_domains.txt')
with open(output_file, 'w', encoding='utf-8') as f:
    for root in final_results:
        f.write(f"{root}\n")

print(f"\n处理后的结果已保存到: {output_file}")

# 保存原始结果（没有*的）
original_file = os.path.join(base_path, 'original_root_domains.txt')
with open(original_file, 'w', encoding='utf-8') as f:
    for root in sorted(all_root_domains):
        f.write(f"{root}\n")

print(f"原始结果（无*）已保存到: {original_file}")