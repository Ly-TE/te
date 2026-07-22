#!/usr/bin/env python
"""
快速验证 /api/qr-decode 路由是否存在
"""
import sys
import os

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

print("=" * 80)
print("🔍 检查所有已注册的路由")
print("=" * 80)

# 查找包含 qr 的路由
qr_routes = []
for rule in app.url_map.iter_rules():
    if 'qr' in str(rule).lower() or 'decode' in str(rule).lower():
        qr_routes.append({
            'route': str(rule),
            'methods': ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'})),
            'endpoint': rule.endpoint
        })

if qr_routes:
    print("✅ 找到以下包含 'qr' 或 'decode' 的路由:")
    for route in qr_routes:
        print(f"   📍 {route['route']:30s} 方法：{route['methods']:20s} 端点：{route['endpoint']}")
else:
    print("❌ 未找到任何包含 'qr' 或 'decode' 的路由!")

print("\n" + "=" * 80)
print("📋 完整路由列表:")
print("=" * 80)

all_routes = []
for rule in app.url_map.iter_rules():
    methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
    all_routes.append(f"{str(rule):40s} [{methods:20s}] -> {rule.endpoint}")

# 按路由名称排序
all_routes.sort()

for i, route in enumerate(all_routes[:50], 1):  # 只显示前 50 个
    print(f"{i:3d}. {route}")

if len(all_routes) > 50:
    print(f"... 还有 {len(all_routes) - 50} 个路由")

print("\n" + "=" * 80)
print("🎯 重点检查 /api/qr-decode:")
print("=" * 80)

if '/api/qr-decode' in [str(rule) for rule in app.url_map.iter_rules()]:
    print("✅ ✅ ✅  /api/qr-decode 路由已存在!")
    for rule in app.url_map.iter_rules():
        if str(rule) == '/api/qr-decode':
            methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
            print(f"   路径：{rule}")
            print(f"   方法：{methods}")
            print(f"   端点：{rule.endpoint}")
else:
    print("❌ ❌ ❌  /api/qr-decode 路由不存在!")
    print("\n最接近的路由:")
    for rule in app.url_map.iter_rules():
        if 'api' in str(rule).lower():
            print(f"   {rule}")

print("=" * 80)
