#!/bin/bash
# Tool Box Front 部署脚本1

set -e  # 遇到错误时退出

# 配置变量
PROJECT_NAME="tool_box_front"
PROJECT_DIR="/opt/${PROJECT_NAME}"
VENV_DIR="${PROJECT_DIR}/venv"
USER="www-data"
GROUP="www-data"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 检查是否以root权限运行
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "此脚本需要root权限运行"
        exit 1
    fi
}

# 安装系统依赖
install_system_deps() {
    log "安装系统依赖..."
    
    if command -v apt-get &> /dev/null; then
        # Ubuntu/Debian
        apt-get update
        apt-get install -y python3 python3-pip python3-venv python3-dev \
                          build-essential libmysqlclient-dev \
                          nginx supervisor git
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        yum update -y
        yum install -y python3 python3-pip python3-devel \
                      gcc mysql-devel nginx supervisor git
    else
        error "不支持的操作系统"
        exit 1
    fi
}

# 创建项目目录
setup_directories() {
    log "创建项目目录..."
    
    mkdir -p ${PROJECT_DIR}
    mkdir -p /var/log/${PROJECT_NAME}
    mkdir -p /var/run/${PROJECT_NAME}
    
    chown ${USER}:${GROUP} ${PROJECT_DIR}
    chown ${USER}:${GROUP} /var/log/${PROJECT_NAME}
    chown ${USER}:${GROUP} /var/run/${PROJECT_NAME}
}

# 创建Python虚拟环境
setup_virtualenv() {
    log "创建Python虚拟环境..."
    
    cd ${PROJECT_DIR}
    python3 -m venv ${VENV_DIR}
    source ${VENV_DIR}/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    if [ -f "requirements-full.txt" ]; then
        pip install -r requirements-full.txt
    elif [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        error "未找到requirements文件"
        exit 1
    fi
}

# 配置环境变量
setup_env() {
    log "配置环境变量..."
    
    if [ -f ".env.example" ]; then
        cp .env.example .env
        warning "请编辑 .env 文件配置正确的环境变量"
    fi
}

# 配置系统服务
setup_systemd_service() {
    log "配置systemd服务..."
    
    cat > /etc/systemd/system/${PROJECT_NAME}.service << EOF
[Unit]
Description=Tool Box Front Application
After=network.target mysql.service

[Service]
Type=simple
User=${USER}
Group=${GROUP}
WorkingDirectory=${PROJECT_DIR}
Environment=PATH=${VENV_DIR}/bin
ExecStart=${VENV_DIR}/bin/python run.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
}

# 配置Nginx
setup_nginx() {
    log "配置Nginx..."
    
    cat > /etc/nginx/sites-available/${PROJECT_NAME} << EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        client_max_body_size 100M;
    }
    
    location /static/ {
        alias ${PROJECT_DIR}/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

    # 启用站点
    ln -sf /etc/nginx/sites-available/${PROJECT_NAME} /etc/nginx/sites-enabled/
    nginx -t && systemctl reload nginx
}

# 配置日志轮转
setup_logrotate() {
    log "配置日志轮转..."
    
    cat > /etc/logrotate.d/${PROJECT_NAME} << EOF
/var/log/${PROJECT_NAME}/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ${USER} ${GROUP}
    postrotate
        systemctl reload ${PROJECT_NAME}
    endscript
}
EOF
}

# 启动服务
start_services() {
    log "启动服务..."
    
    systemctl start ${PROJECT_NAME}
    systemctl enable ${PROJECT_NAME}
    
    # 检查服务状态
    sleep 5
    if systemctl is-active --quiet ${PROJECT_NAME}; then
        log "服务启动成功"
    else
        error "服务启动失败"
        systemctl status ${PROJECT_NAME}
        exit 1
    fi
}

# 主部署流程
main() {
    log "开始部署 ${PROJECT_NAME}..."
    
    check_root
    install_system_deps
    setup_directories
    setup_virtualenv
    setup_env
    setup_systemd_service
    setup_nginx
    setup_logrotate
    start_services
    
    log "部署完成！"
    log "应用地址: http://your-server-ip"
    log "日志文件: /var/log/${PROJECT_NAME}/"
    log "请确保配置正确的环境变量和数据库连接"
}

# 执行部署
main "$@"