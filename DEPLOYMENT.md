# Tool Box Front 项目部署指南

## 项目概述
这是一个基于Flask的Web应用，提供多种工具功能，包括：
- OCPC数据查询
- SDK日志解密
- 用户时长管理
- 账号注册功能
- 统一登录认证

## 系统要求

### 操作系统
- Linux (推荐 Ubuntu 20.04+/CentOS 7+)
- Windows Server 2016+
- macOS 10.15+

### 软件依赖
- Python 3.8+
- MySQL 5.7+ 或 MariaDB 10.3+
- Node.js (可选，用于前端构建)

## 必需的Python依赖包

### 核心依赖
```bash
Flask==2.3.3
Flask-CORS==4.0.0
PyMySQL==1.1.0
DBUtils==3.0.2
python-dotenv==1.0.0
requests==2.31.0
```

### 可选依赖（根据功能需求）
```bash
# 加密相关
pycryptodome==3.19.0  # AES加密解密

# 数据处理
pandas==2.0.3         # 数据分析
numpy==1.24.3         # 数值计算

# 日志处理
loguru==0.7.0         # 高级日志库

# 缓存
redis==5.0.1          # Redis客户端
```

## 部署步骤

### 1. 环境准备
```bash
# 创建项目目录
mkdir /opt/tool_box_front
cd /opt/tool_box_front

# 创建Python虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 升级pip
pip install --upgrade pip
```

### 2. 安装依赖
```bash
# 安装核心依赖
pip install -r requirements.txt

# 如果需要额外功能，安装可选依赖
pip install pycryptodome pandas numpy loguru redis
```

### 3. 数据库配置

#### 创建数据库用户和权限
```sql
-- 创建数据库用户
CREATE USER 'your_db_user'@'%' IDENTIFIED BY 'your_db_password';
GRANT ALL PRIVILEGES ON leigod_config.* TO 'your_db_user'@'%';
GRANT ALL PRIVILEGES ON leigod_statistics.* TO 'your_db_user'@'%';
FLUSH PRIVILEGES;
```

#### 创建环境配置文件
在项目根目录创建 `.env` 文件：

```env
# 环境配置
ENVIRONMENT=production
DEBUG=False

# 数据库配置
TEST_DB_HOST=your-test-db-host
TEST_DB_PORT=33506
TEST_DB_USER=your-test-db-user
TEST_DB_PASSWORD=your-test-db-password
TEST_DB_CHARSET=utf8mb4

# 安全配置
SECRET_KEY=your-secret-key-here-change-this-in-production

# 分页配置
DEFAULT_PAGE_SIZE=100
MAX_PAGE_SIZE=1000

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/var/log/tool_box_front/app.log
```

### 4. 服务配置

#### 创建系统服务 (Linux systemd)
创建文件 `/etc/systemd/system/tool_box_front.service`：

```ini
[Unit]
Description=Tool Box Front Application
After=network.target mysql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/tool_box_front
Environment=PATH=/opt/tool_box_front/venv/bin
ExecStart=/opt/tool_box_front/venv/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 启动服务
```bash
# 重新加载systemd配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start tool_box_front

# 设置开机自启
sudo systemctl enable tool_box_front

# 查看服务状态
sudo systemctl status tool_box_front
```

### 5. 反向代理配置 (推荐使用Nginx)

#### Nginx配置文件
创建 `/etc/nginx/sites-available/tool_box_front`：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL证书配置
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    # SSL安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # 客户端上传文件大小限制
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # 静态文件缓存
    location /static/ {
        alias /opt/tool_box_front/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### 启用站点
```bash
sudo ln -s /etc/nginx/sites-available/tool_box_front /etc/nginx/sites-enabled/
sudo nginx -t  # 测试配置
sudo systemctl reload nginx
```

### 6. 日志管理

#### 创建日志目录
```bash
sudo mkdir -p /var/log/tool_box_front
sudo chown www-data:www-data /var/log/tool_box_front
```

#### 配置日志轮转
创建 `/etc/logrotate.d/tool_box_front`：

```bash
/var/log/tool_box_front/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload tool_box_front
    endscript
}
```

## 监控和维护

### 健康检查端点
应用提供以下健康检查端点：
- `/health` - 应用健康状态
- `/api/v1/health` - API健康状态

### 监控脚本示例
```bash
#!/bin/bash
# health_check.sh

APP_URL="http://localhost:5000/health"
TIMEOUT=10

if curl -f --max-time $TIMEOUT $APP_URL > /dev/null 2>&1; then
    echo "Application is healthy"
    exit 0
else
    echo "Application is unhealthy"
    # 重启服务
    sudo systemctl restart tool_box_front
    exit 1
fi
```

### 定期维护任务
```bash
# 清理临时文件
0 2 * * * find /tmp -name "*.tmp" -mtime +7 -delete

# 数据库连接池健康检查
*/30 * * * * /opt/tool_box_front/scripts/db_health_check.py
```

## 安全配置

### 防火墙设置
```bash
# 只开放必要端口
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

### 应用安全配置
- 定期更新依赖包
- 使用强密码策略
- 限制数据库访问权限
- 启用HTTPS
- 配置适当的CORS策略

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库服务状态
   - 验证数据库连接参数
   - 确认网络连通性

2. **应用启动失败**
   - 查看应用日志：`/var/log/tool_box_front/app.log`
   - 检查依赖包是否完整安装
   - 验证配置文件语法

3. **性能问题**
   - 检查系统资源使用情况
   - 优化数据库查询
   - 调整连接池配置

### 日志查看
```bash
# 实时查看应用日志
sudo tail -f /var/log/tool_box_front/app.log

# 查看Nginx访问日志
sudo tail -f /var/log/nginx/access.log

# 查看Nginx错误日志
sudo tail -f /var/log/nginx/error.log
```

## 备份策略

### 数据库备份
```bash
#!/bin/bash
# backup_db.sh

BACKUP_DIR="/backup/mysql"
DATE=$(date +%Y%m%d_%H%M%S)

mysqldump -h "$TEST_DB_HOST" -P "$TEST_DB_PORT" -u "$TEST_DB_USER" -p leigod_config > $BACKUP_DIR/config_$DATE.sql
mysqldump -h "$TEST_DB_HOST" -P "$TEST_DB_PORT" -u "$TEST_DB_USER" -p leigod_statistics > $BACKUP_DIR/statistics_$DATE.sql

# 压缩备份文件
gzip $BACKUP_DIR/*_$DATE.sql

# 删除7天前的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
```

### 应用代码备份
```bash
# 备份应用代码
tar -czf /backup/tool_box_front_$(date +%Y%m%d).tar.gz /opt/tool_box_front
```

## 升级步骤

### 应用升级
```bash
# 停止服务
sudo systemctl stop tool_box_front

# 备份当前版本
cp -r /opt/tool_box_front /opt/tool_box_front_backup_$(date +%Y%m%d)

# 部署新版本
cd /opt/tool_box_front
git pull origin main  # 或其他版本控制方式

# 安装新依赖
pip install -r requirements.txt

# 重启服务
sudo systemctl start tool_box_front
```

## 联系支持
如有部署问题，请联系系统管理员或查看项目文档。