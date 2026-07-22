# Flask应用部署和运维完整指南

## 📋 项目概述

这是一个完整的Flask Web应用，包含OCPC查询、用户渠道管理等功能，已配备完整的部署和管理脚本。

## 🚀 部署到远程服务器 (192.168.3.101)

### 1. 使用自动化部署脚本

```bash
# 给脚本添加执行权限
chmod +x deploy_to_server.sh

# 完整部署到远程服务器
./deploy_to_server.sh deploy root@192.168.3.101
```

### 2. 手动部署步骤

#### 2.1 传输代码到服务器
```bash
# 方法1: 使用SCP
scp -r /path/to/tool_box_front root@192.168.3.101:/root/

# 方法2: 使用rsync
rsync -avz -e ssh /path/to/tool_box_front/ root@192.168.3.101:/root/tool_box_front/
```

#### 2.2 在服务器上安装依赖
```bash
ssh root@192.168.3.101

# 进入项目目录
cd /root/tool_box_front

# 设置执行权限
chmod +x *.sh

# 安装依赖
./install_service.sh
```

#### 2.3 配置环境变量
```bash
# 编辑配置文件
nano .env

# 示例配置
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=your-very-secure-secret-key-here
DB_HOST=your-database-host
DB_PORT=3306
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_NAME=your-db-name
DEBUG=False
PORT=5000
HOST=0.0.0.0
```

#### 2.4 启动服务
```bash
# 启动服务
./start_service.sh start

# 检查状态
./status_service.sh status
```

## 🔧 解决常见问题

### OpenSSL兼容性问题

如果遇到以下错误：
```
urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'OpenSSL 1.0.2k-fips'
```

#### 解决方案1: 使用修复脚本
```bash
# 给修复脚本添加执行权限
chmod +x fix_openssl_issue.sh

# 修复OpenSSL兼容性问题
./fix_openssl_issue.sh fix-openssl root@192.168.3.101

# 或者执行完整修复流程
./fix_openssl_issue.sh full-fix root@192.168.3.101
```

#### 解决方案2: 手动修复
```bash
# 激活虚拟环境
source /root/tool_box_front/venv/bin/activate

# 降级urllib3
pip install 'urllib3<2.0.0'

# 重启服务
./restart_service.sh restart
```

## 🛠 服务管理命令

### 基础管理
```bash
# 启动服务
./start_service.sh start

# 停止服务
./stop_service.sh stop

# 重启服务
./restart_service.sh restart

# 查看状态
./status_service.sh status
```

### 日志管理
```bash
# 查看访问日志
./logs_service.sh access 100

# 查看错误日志
./logs_service.sh error 50

# 实时监控日志
./logs_service.sh follow all

# 搜索日志
./logs_service.sh search "error"

# 查看日志统计
./logs_service.sh stats
```

### 交互式管理
```bash
# 启动交互式管理界面
./manage_service.sh
```

## 🏗 生产环境配置

### 1. 使用Gunicorn作为WSGI服务器

```bash
# 安装Gunicorn
source venv/bin/activate
pip install gunicorn

# 创建Gunicorn配置
cat > gunicorn.conf.py << 'EOF'
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
preload_app = True
EOF

# 使用Gunicorn启动
gunicorn -c gunicorn.conf.py app:app
```

### 2. 配置Systemd服务

创建systemd服务文件：
```bash
sudo nano /etc/systemd/system/tool_box_front.service
```

内容：
```ini
[Unit]
Description=Flask Web Application - tool_box_front
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/root/tool_box_front
Environment=PATH=/root/tool_box_front/venv/bin
ExecStart=/root/tool_box_front/venv/bin/gunicorn -c /root/tool_box_front/gunicorn.conf.py app:app
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=tool_box_front

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable tool_box_front.service
sudo systemctl start tool_box_front.service
```

### 3. Nginx反向代理配置

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
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /static {
        alias /root/tool_box_front/static;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
```

## 🔐 安全配置

### 1. 文件权限设置
```bash
# 设置适当的文件权限
sudo chown -R root:root /root/tool_box_front
sudo chmod -R 755 /root/tool_box_front
sudo chmod 600 /root/tool_box_front/.env
```

### 2. 防火墙配置
```bash
# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

## 📊 监控和维护

### 服务监控
```bash
# 查看服务状态
sudo systemctl status tool_box_front.service

# 查看服务日志
sudo journalctl -u tool_box_front.service -f

# 查看系统资源使用
htop
```

### 日志轮转
```bash
sudo nano /etc/logrotate.d/tool_box_front
```

内容：
```
/root/tool_box_front/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    copytruncate
    postrotate
        systemctl reload tool_box_front.service > /dev/null 2>&1 || true
    endscript
}
```

## 💾 备份策略

创建备份脚本：
```bash
sudo nano /root/backup_tool_box.sh
```

内容：
```bash
#!/bin/bash
BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份配置文件
cp /root/tool_box_front/.env $BACKUP_DIR/.env.backup.$DATE

# 清理超过30天的备份
find $BACKUP_DIR -name "*.backup.*" -mtime +30 -delete
```

设置定时备份：
```bash
crontab -e
# 添加每日凌晨2点备份
0 2 * * * /root/backup_tool_box.sh
```

## 🎯 总结

您的Flask应用已经成功部署在192.168.3.101服务器上，运行在5000端口。通过我们的自动化脚本，您可以轻松管理服务的启动、停止、重启和监控。OpenSSL兼容性问题也已解决，确保应用能够稳定运行。

访问地址：
- 直接访问：http://192.168.3.101:5000
- 通过Nginx（如配置）：http://192.168.3.101