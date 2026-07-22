#!/bin/bash

# ============================================
# Flask Web服务安装脚本
# 用于在Linux系统下初始化和安装服务环境
# ============================================

# 设置脚本基本配置
set -e
set -u

#基本变量配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="tool_box_front"

#输出函数
print_info() {
    echo -e "\033[32m[INFO]\033[0m $1"
}

print_warn() {
    echo -e "\033[33m[WARN]\033[0m $1"
}

print_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

print_success() {
    echo -e "\033[32m[SUCCESS]\033[0m $1"
}

#检查系统依赖
check_system_dependencies() {
    print_info "检查系统依赖..."
    
    # 检查基本命令
    local required_commands=("python3" "pip3" "git" "curl" "wget")
    local missing_commands=()
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_commands+=("$cmd")
        fi
    done
    
    if [[ ${#missing_commands[@]} -gt 0 ]]; then
        print_warn "缺少以下系统命令: ${missing_commands[*]}"
        print_info "请使用以下命令安装:"
        if command -v apt-get &> /dev/null; then
            echo "sudo apt-get update && sudo apt-get install -y ${missing_commands[*]}"
        elif command -v yum &> /dev/null; then
            echo "sudo yum install -y ${missing_commands[*]}"
        elif command -v dnf &> /dev/null; then
            echo "sudo dnf install -y ${missing_commands[*]}"
        fi
        return 1
    fi
    
    print_success "系统依赖检查完成"
    return 0
}

#安装Python虚拟环境
install_python_venv() {
    print_info "安装Python虚拟环境支持..."
    
    if ! python3 -m venv --help &> /dev/null; then
        print_warn "Python venv模块不可用，正在安装..."
        
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y python3-venv python3-dev
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3-virtualenv python3-devel
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y python3-virtualenv python3-devel
        else
            print_error "无法自动安装venv，请手动安装python3-venv"
            return 1
        fi
    fi
    
    print_success "Python虚拟环境支持已安装"
    return 0
}

#创建虚拟环境
create_virtual_environment() {
    print_info "创建Python虚拟环境..."
    
    if [[ -d "$SCRIPT_DIR/venv" ]]; then
        print_warn "虚拟环境已存在，跳过创建"
        return 0
    fi
    
    python3 -m venv "$SCRIPT_DIR/venv"
    print_success "虚拟环境创建成功"
    return 0
}

#安装Python依赖
install_python_dependencies() {
    print_info "安装Python依赖包..."
    
    #激活虚拟环境
    source "$SCRIPT_DIR/venv/bin/activate"
    
    #升级pip
    pip3 install --upgrade pip --quiet
    
    #安装依赖
    if [[ -f "$SCRIPT_DIR/requirements.txt" ]]; then
        pip3 install -r "$SCRIPT_DIR/requirements.txt" --quiet
        print_success "Python依赖包安装完成"
    else
        print_warn "未找到requirements.txt文件，跳过依赖安装"
    fi
    
    return 0
}

#配置环境文件
configure_environment() {
    print_info "配置环境文件..."
    
    local env_file="$SCRIPT_DIR/.env"
    local env_example="$SCRIPT_DIR/.env.example"
    
    if [[ ! -f "$env_file" ]]; then
        if [[ -f "$env_example" ]]; then
            cp "$env_example" "$env_file"
            print_success "环境文件已创建: $env_file"
            print_info "请编辑此文件配置数据库连接等参数"
        else
            print_warn "未找到环境配置示例文件"
            #创建基本的环境文件
            cat > "$env_file" << EOF
# Flask应用配置
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=your-secret-key-here

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_db_name

#应用配置
DEBUG=False
PORT=5000
HOST=0.0.0.0
EOF
            print_success "已创建基本环境配置文件"
            print_info "请编辑 $env_file 文件配置正确的参数"
        fi
    else
        print_info "环境文件已存在: $env_file"
    fi
    
    return 0
}

#创建日志目录
create_log_directory() {
    print_info "创建日志目录..."
    
    mkdir -p "$SCRIPT_DIR/logs"
    chmod 755 "$SCRIPT_DIR/logs"
    
    print_success "日志目录创建完成: $SCRIPT_DIR/logs"
    return 0
}

#设置脚本权限
set_script_permissions() {
    print_info "设置脚本执行权限..."
    
    local scripts=(
        "start_service.sh"
        "stop_service.sh"
        "restart_service.sh"
        "status_service.sh"
        "logs_service.sh"
        "manage_service.sh"
        "install_service.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [[ -f "$SCRIPT_DIR/$script" ]]; then
            chmod +x "$SCRIPT_DIR/$script"
        fi
    done
    
    print_success "脚本权限设置完成"
    return 0
}

#创建系统服务文件(可选)
create_systemd_service() {
    local create_service=${1:-false}
    
    if [[ "$create_service" != "true" ]]; then
        return 0
    fi
    
    print_info "创建systemd服务文件..."
    
    local service_file="/etc/systemd/system/${APP_NAME}.service"
    local service_content="[Unit]
Description=Flask Web Application - ${APP_NAME}
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=${SCRIPT_DIR}
Environment=PATH=${SCRIPT_DIR}/venv/bin
ExecStart=${SCRIPT_DIR}/venv/bin/python3 ${SCRIPT_DIR}/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target"
    
    #检查是否有sudo权限
    if sudo -v 2>/dev/null; then
        echo "$service_content" | sudo tee "$service_file" > /dev/null
        sudo systemctl daemon-reload
        print_success "systemd服务文件创建完成: $service_file"
        print_info "使用以下命令管理服务:"
        echo "  sudo systemctl start ${APP_NAME}.service"
        echo "  sudo systemctl stop ${APP_NAME}.service"
        echo "  sudo systemctl status ${APP_NAME}.service"
    else
        print_warn "没有sudo权限，跳过systemd服务创建"
        print_info "服务文件内容如下，可手动创建:"
        echo "----------------------------------------"
        echo "$service_content"
        echo "----------------------------------------"
    fi
    
    return 0
}

#显示安装完成信息
show_completion_message() {
    print_success "服务安装完成！"
    echo ""
    echo "========================================"
    echo "下一步操作:"
    echo "1.编辑配置文件: $SCRIPT_DIR/.env"
    echo "2.启动服务: $SCRIPT_DIR/start_service.sh start"
    echo "3. 查看状态: $SCRIPT_DIR/status_service.sh status"
    echo "4.管服务: $SCRIPT_DIR/manage_service.sh"
    echo ""
    echo "服务管理命令:"
    echo "  启动: $SCRIPT_DIR/start_service.sh start"
    echo " 停: $SCRIPT_DIR/stop_service.sh stop"
    echo "  重启: $SCRIPT_DIR/restart_service.sh restart"
    echo "  状态: $SCRIPT_DIR/status_service.sh status"
    echo "  日志: $SCRIPT_DIR/logs_service.sh"
    echo " 管: $SCRIPT_DIR/manage_service.sh"
    echo "========================================"
}

#显示使用帮助
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  install             完整安装 (默认)"
    echo "  check               检查依赖环境"
    echo "  venv                 创建虚拟环境"
    echo "  deps                安装Python依赖"
    echo "  config              配置环境文件"
    echo "  systemd              创建systemd服务文件"
    echo "  help                显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 install           #完整安装所有组件"
    echo "  $0 check             # 仅检查依赖环境"
    echo "  $0 systemd           # 创建systemd服务文件"
}

# 主程序入口
main() {
    case "${1:-install}" in
        install)
            print_info "开始安装 $APP_NAME 服务..."
            
            #检查系统依赖
            if ! check_system_dependencies; then
                print_error "系统依赖检查失败，请先安装缺失的依赖"
                exit 1
            fi
            
            #安装Python虚拟环境支持
            install_python_venv || exit 1
            
            # 创建虚拟环境
            create_virtual_environment || exit 1
            
            #安装Python依赖
            install_python_dependencies || exit 1
            
            #配置环境文件
            configure_environment || exit 1
            
            # 创建日志目录
            create_log_directory || exit 1
            
            # 设置脚本权限
            set_script_permissions || exit 1
            
            # 询问是否创建systemd服务
            read -p "是否创建systemd服务文件? (y/N): " create_systemd
            if [[ "$create_systemd" =~ ^[Yy]$ ]]; then
                create_systemd_service "true"
            fi
            
            #显示完成信息
            show_completion_message
            ;;
            
        check)
            check_system_dependencies
            ;;
            
        venv)
            install_python_venv
            create_virtual_environment
            ;;
            
        deps)
            if [[ ! -d "$SCRIPT_DIR/venv" ]]; then
                print_error "虚拟环境不存在，请先运行: $0 venv"
                exit 1
            fi
            install_python_dependencies
            ;;
            
        config)
            configure_environment
            ;;
            
        systemd)
            create_systemd_service "true"
            ;;
            
        help|--help|-h)
            show_help
            ;;
            
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

#执行主程序
main "$@"