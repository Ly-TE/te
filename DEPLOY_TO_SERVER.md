# 部署到远程服务器指南

## 准备工作

### 1. 确认服务器访问权限
```bash
# 测试服务器连接
ssh username@192.168.3.101

# 如果需要密码，后续命令中添加 -o PubkeyAuthentication=no
```

### 2. 确保服务器具备必要软件
```bash
# 在服务器上检查必要软件
ssh username@192.168.3.101 "python3 --version && pip3 --version && git --version"
```

## 部署步骤

### 方法一：使用SCP传输代码（推荐）

#### 1. 将整个项目传输到服务器
```bash
# 从本地机器执行
scp -r E:\te\tool_box_front username@192.168.3.101:/home/username/
```

#### 2. SSH到服务器并部署
```bash
# 连接到服务器
ssh username@192.168.3.101

# 进入项目目录
cd /home/username/tool_box_front

# 使用我们提供的安装脚本
chmod +x *.sh
./install_service.sh

# 配置环境变量
nano .env  # 编辑配置文件，设置正确的数据库和其他配置
```

### 方法二：使用Git（如果您有代码仓库）

#### 1. 在服务器上克隆代码
```bash
# 在服务器上执行
ssh username@192.168.3.101

# 克隆代码（假设您已将代码上传到Git仓库）
git clone <your-git-repo-url> /home/username/tool_box_front
cd /home/username/tool_box_front
```

### 方法三：压缩传输

#### 1. 本地打包
```bash
# 在本地打包项目
cd E:\te
tar -czf tool_box_front.tar.gz tool_box_front/
```

#### 2. 传输到服务器
```bash
# 传输压缩包
scp tool_box_front.tar.gz username@192.168.3.101:/home/username/

# SSH到服务器解压
ssh username@192.168.3.101 "cd /home/username && tar -xzf tool_box_front.tar.gz"
```

## 服务器配置步骤

### 1. SSH连接到服务器
```bash
ssh username@192.168.3.101
```

### 2. 更新系统并安装必要软件
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git nginx

# CentOS/RHEL
# sudo yum update
# sudo yum install -y python3 python3-pip python3-venv git nginx
```

### 3. 进入项目目录并设置权限
```bash
cd /home/username/tool_box_front
chmod +x *.sh
```

### 4. 安装依赖并配置服务
```bash
# 运行安装脚本
./install_service.sh

# 编辑配置文件（重要！）
nano .env
```

### 5. 配置.env文件
```bash
# 示例配置，请根据实际情况修改
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

### 6. 启动服务
```bash
# 启动服务
./start_service.sh start

# 检查服务状态
./status_service.sh status
```

## 使用systemd服务（推荐，长期运行）

### 1. 创建systemd服务文件
```bash
sudo nano /etc/systemd/system/tool_box_front.service
```

### 2. 添加以下内容（请根据实际情况修改路径和用户名）
```ini
[Unit]
Description=Flask Web Application - tool_box_front
After=network.target

[Service]
Type=simple
User=username
WorkingDirectory=/home/username/tool_box_front
Environment=PATH=/home/username/tool_box_front/venv/bin
ExecStart=/home/username/tool_box_front/venv/bin/python3 /home/username/tool_box_front/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. 启用并启动服务
```bash
sudo systemctl daemon-reload
sudo systemctl enable tool_box_front.service
sudo systemctl start tool_box_front.service
sudo systemctl status tool_box_front.service
```

## Nginx反向代理配置（可选但推荐）

### 1. 配置Nginx
```bash
sudo nano /etc/nginx/sites-available/tool_box_front
```

### 2. 添加配置
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

### 3. 启用站点
```bash
sudo ln -s /etc/nginx/sites-available/tool_box_front /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 防火墙配置

### 1. 开放端口（如果启用了防火墙）
```bash
# UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 5000/tcp  # 如果直接访问Flask端口

# 或者 iptables
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
```

## 验证部署

### 1. 检查服务是否运行
```bash
./status_service.sh status
```

### 2. 访问应用
- 直接访问：http://192.168.3.101:5000
- 通过Nginx：http://192.168.3.101

### 3. 查看日志
```bash
./logs_service.sh access
./logs_service.sh error
```

## 常见问题排查

### 1. 端口被占用
```bash
# 检查端口占用
sudo netstat -tlnp | grep :5000
# 或
sudo ss -tlnp | grep :5000
```

### 2. 权限问题
```bash
# 确保项目目录权限正确
chown -R username:username /home/username/tool_box_front
```

### 3. 数据库连接问题
```bash
# 检查数据库配置
cat .env | grep DB_
```

## 维护命令

```bash
# 重启服务
./restart_service.sh restart

# 停止服务
./stop_service.sh stop

# 查看实时日志
./logs_service.sh follow all
```

请根据您的具体情况调整用户名、路径和配置参数。