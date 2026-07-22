#!/usr/bin/env python
"""
直接启动 app.py - 确保加载最新代码
"""
import sys
import os

# 清理 Python 缓存
for cache_dir in ['__pycache__', '.pytest_cache']:
    cache_path = os.path.join(os.path.dirname(__file__), cache_dir)
    if os.path.exists(cache_path):
        import shutil
        shutil.rmtree(cache_path)
        print(f"✅ 已清理缓存目录：{cache_path}")

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🚀 正在启动 Flask 服务 (直接模式)")
print("=" * 80)

# 直接执行 app.py 的 main 块
exec(open('app.py', encoding='utf-8').read())
