# 解决 http://192.168.3.101:5000 无法访问的问题

## 快速解决方案

### 方案1：使用快速修复脚本（推荐）

```bash
# 1. 给脚本添加执行权限
chmod +x quick_fix_access.sh

# 2. 运行快速修复
./quick_fix_access.sh quick-fix root@192.168.3.101
```

### 方案2：使用诊断脚本

```bash
# 1. 给脚本添加执行权限
chmod +x diagnose_connection.sh

# 2. 诊断问题
./diagnose_connection.sh diagnose root@192.168.3.101

# 3. 修复所有问题
./diagnose_connection.sh fix-all root@192.168.3.101
```

## 手动检查步骤

如果上述脚本无法解决问题，请按以下步骤手动检查：

### 1. 检查服务状态
```bash
# SSH到服务器
ssh root@192.168.3.101

# 检查服务是否运行
cd /root/tool_box_front
./status_service.sh status
```

### 2. 检查端口监听
```bash
# 检查5000端口是否在监听
netstat -tlnp | grep :5000
# 或
ss -tlnp | grep :5000
```

### 3. 检查防火墙
```bash
# 检查防火墙状态
sudo firewall-cmd --list-ports
# 或
sudo iptables -L -n | grep 5000
```

### 4. 重启服务
```bash
# 停止服务
./stop_service.sh stop

# 等待几秒
sleep 3

# 启动服务
./start_service.sh start

# 检查状态
./status_service.sh status
```

## 常见原因

1. **服务未启动** - Flask应用没有正确启动
2. **防火墙阻止** - 防火墙规则阻止了5000端口
3. **端口冲突** - 5000端口被其他服务占用
4. **绑定地址问题** - 服务只绑定到了localhost而非所有接口

## 验证修复

修复完成后，等待1-2分钟让服务完全启动，然后：

1. 从服务器本地测试：
   ```bash
   curl -I localhost:5000
   ```

2. 从浏览器访问：
   ```
   http://192.168.3.101:5000
   ```

如果仍然无法访问，请查看服务日志：
```bash
./logs_service.sh error 50
```

## 长期解决方案

对于生产环境，建议：
1. 使用Nginx作为反向代理
2. 配置systemd服务实现开机自启
3. 设置适当的防火墙规则
4. 监控服务状态

请先尝试快速修复脚本，它会自动处理大部分常见问题。