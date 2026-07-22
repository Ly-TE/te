# 服务连接问题故障排除指南

## 问题描述
无法访问 http://192.168.3.101:5000

## 可能的原因及解决方案

### 1. 服务未正确启动

#### 检查服务状态
```bash
# SSH到服务器
ssh root@192.168.3.101

# 进入项目目录
cd /root/tool_box_front

# 检查服务状态
./status_service.sh status

# 或者直接检查进程
ps aux | grep -i 'python.*app\.py\|gunicorn' | grep -v grep
```

#### 重启服务
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

### 2. 防火墙阻止连接

#### 检查防火墙状态
```bash
# 检查firewalld
sudo systemctl status firewalld

# 检查端口是否开放
sudo firewall-cmd --list-ports
```

#### 开放端口
```bash
# 使用firewalld
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload

# 或者使用iptables
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
```

### 3. 服务绑定地址问题

#### 检查服务绑定地址
Flask应用可能只绑定到了localhost，而不是所有接口。

检查app.py中的启动参数：
```python
# 确保使用以下参数启动
app.run(host='0.0.0.0', port=5000)
```

或者在生产环境中使用Gunicorn：
```bash
gunicorn -b 0.0.0.0:5000 app:app
```

### 4. 网络连接问题

#### 测试本地连接
```bash
# 在服务器上测试本地连接
curl -I localhost:5000

# 检查端口监听
netstat -tlnp | grep :5000
# 或
ss -tlnp | grep :5000
```

#### 测试外部连接
```bash
# 从其他机器测试连接
telnet 192.168.3.101 5000
# 或
nc -zv 192.168.3.101 5000
```

### 5. 使用诊断脚本

运行我们提供的诊断脚本：
```bash
# 给脚本添加执行权限
chmod +x diagnose_connection.sh

# 诊断连接问题
./diagnose_connection.sh diagnose root@192.168.3.101

# 或者直接检查服务状态
./diagnose_connection.sh check-service root@192.168.3.101

# 修复所有常见问题
./diagnose_connection.sh fix-all root@192.168.3.101
```

### 6. 日志检查

检查服务日志以查找错误信息：
```bash
# 查看访问日志
./logs_service.sh access 50

# 查看错误日志
./logs_service.sh error 50

# 实时监控日志
./logs_service.sh follow all
```

### 7. 服务配置检查

检查.env配置文件：
```bash
cat .env | grep -E "(HOST|PORT)"
```

确保HOST设置为'0.0.0.0'而不是'127.0.0.1'或'localhost'。

### 8. 完整修复步骤

如果仍然无法访问，请按以下步骤操作：

```bash
# 1. SSH到服务器
ssh root@192.168.3.101

# 2. 进入项目目录
cd /root/tool_box_front

# 3. 停止服务
./stop_service.sh stop

# 4. 检查是否有残留进程
ps aux | grep -i 'python.*app\.py' | awk '{print $2}' | xargs kill -9 2>/dev/null || true

# 5. 检查端口是否已释放
netstat -tlnp | grep :5000

# 6. 开放防火墙端口
sudo firewall-cmd --permanent --add-port=5000/tcp 2>/dev/null || true
sudo firewall-cmd --reload 2>/dev/null || true

# 7. 启动服务
./start_service.sh start

# 8. 等待服务启动
sleep 10

# 9. 检查服务状态
./status_service.sh status

# 10. 测试本地连接
curl -I localhost:5000
```

### 9. 生产环境建议

对于生产环境，建议使用Gunicorn+Nginx的组合：

#### 使用Gunicorn
```bash
# 安装Gunicorn
source venv/bin/activate
pip install gunicorn

# 创建配置文件
cat > gunicorn.conf.py << 'EOF'
bind = "0.0.0.0:5000"
workers = 4
timeout = 120
EOF

# 使用Gunicorn启动
gunicorn -c gunicorn.conf.py app:app
```

#### 配置Nginx
```bash
sudo nano /etc/nginx/conf.d/tool_box_front.conf
```

内容：
```nginx
server {
    listen 80;
    server_name 192.168.3.101;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 10. 验证修复

修复完成后，验证服务是否可访问：
- 从服务器本地：`curl -I localhost:5000`
- 从服务器外部：浏览器访问 `http://192.168.3.101:5000`
- 检查端口监听：`netstat -tlnp | grep :5000`

如果按照以上步骤操作后仍然无法访问，请检查：
- 网络路由和交换机配置
- 服务器的安全组设置（如果是云服务器）
- 本地网络连接和防火墙设置