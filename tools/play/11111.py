import redis

# Redis 连接信息
redis_host = '172.31.16.3'
redis_port = 32187
redis_password = 'LbCn_jMT8NGp8x2NyL9'

# 连接 Redis
r = redis.Redis(host=redis_host, port=redis_port, password=redis_password, db=0)

# 要匹配的键名前缀
key_prefix = 'app:retain:popup:click'

# 获取所有匹配的键
matching_keys = r.keys(f'{key_prefix}*')

if matching_keys:
    # 删除所有匹配的键
    r.delete(*matching_keys)
    print(f"已成功删除以 {key_prefix} 开头的 {len(matching_keys)} 个键。")
else:
    print(f"未找到以 {key_prefix} 开头的键。")