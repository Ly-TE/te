#!/bin/bash

# ============================================
# Flask Web服务启动脚本
# 用于在Linux系统下启动Flask应用服务
# ============================================

# 设置脚本基本配置
set -e  #错误立即退出
set -u  # 使用未定义变量时报错

#基本变量配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="tool_box_front"
PID_FILE="$SCRIPT_DIR/${APP_NAME}.pid"
LOG_FILE="$SCRIPT_DIR/logs/${APP_NAME}.log"
ERROR_LOG_FILE="$SCRIPT_DIR/logs/${APP_NAME}_error.log"
CONFIG_FILE="$SCRIPT_DIR/.env"

# 创建日志目录
mkdir -p "$SCRIPT_DIR/logs"

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

#检查服务是否已在运行
is_running() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # 服务正在运行
        else
            # PID文件存在但进程不存在，清理PID文件
            rm -f "$PID_FILE"
            return 1  # 服务未运行
        fi
    fi
    return 1  # 服务未运行
}

#检查依赖环境
check_dependencies() {
    print_info "检查依赖环境..."
    
    #检查Python
    if ! command -v python3 &> /dev/null; then
        print_error "未找到Python3，请先安装Python3"
        exit 1
    fi
    
    #检查pip
    if ! command -v pip3 &> /dev/null; then
        print_error "未找到pip3，请先安装pip3"
        exit 1
    fi
    
    # 检查虚拟环境
    if [[ ! -d "$SCRIPT_DIR/venv" ]]; then
        print_warn "未找到虚拟环境，正在创建..."
        python3 -m venv "$SCRIPT_DIR/venv"
    fi
    
    #激活虚拟环境并安装依赖
    source "$SCRIPT_DIR/venv/bin/activate"
    
    if [[ -f "$SCRIPT_DIR/requirements.txt" ]]; then
        print_info "安装Python依赖包..."
        pip3 install -r "$SCRIPT_DIR/requirements.txt" --quiet
    fi
    
    # 检查配置文件
    if [[ ! -f "$CONFIG_FILE" ]]; then
        if [[ -f "$SCRIPT_DIR/.env.example" ]]; then
            print_warn "配置文件不存在，复制示例配置..."
            cp "$SCRIPT_DIR/.env.example" "$CONFIG_FILE"
            print_info "请编辑 $CONFIG_FILE 文件配置数据库等参数"
        else
            print_error "未找到配置文件 .env 或 .env.example"
            exit 1
        fi
    fi
    
    print_success "依赖环境检查完成"
}

#启动服务函数
start_service() {
    # 检查服务是否已在运行
    if is_running; then
        local pid=$(cat "$PID_FILE")
        print_warn "服务已在运行 (PID: $pid)"
        return 0
    fi
    
    print_info "正在启动 $APP_NAME 服务..."
    
    # 检查依赖
    check_dependencies
    
    #激活虚拟环境
    source "$SCRIPT_DIR/venv/bin/activate"
    
    # 设置环境变量
    export FLASK_APP="$SCRIPT_DIR/app.py"
    export FLASK_ENV="production"
    
    #启服务服务 (后台运行)
    nohup python3 "$SCRIPT_DIR/app.py" > "$LOG_FILE" 2> "$ERROR_LOG_FILE" &
    local pid=$!
    
    # 保存PID
    echo "$pid" > "$PID_FILE"
    
    #等待服务启动
    sleep 3
    
    #检查服务是否成功启动
    if ps -p "$pid" > /dev/null 2>&1; then
        print_success "$APP_NAME 服务启动成功 (PID: $pid)"
        print_info "访问地址: http://localhost:5000"
        print_info "日志文件: $LOG_FILE"
        print_info "错误日志: $ERROR_LOG_FILE"
    else
        print_error "服务启动失败，请检查日志文件"
        rm -f "$PID_FILE"
        exit 1
    fi
}

#显示使用帮助
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  start    启动服务"
    echo "  stop     停服务止服务"
    echo "  restart   重启服务"
    echo "  status    查看服务状态"
    echo "  logs      查看服务日志"
    echo "  help     显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start     # 启动服务"
    echo "  $0 status    # 查看服务状态"
    echo "  $0 logs      # 实时查看日志"
}

# 主程序入口
main() {
    case "${1:-help}" in
        start)
            start_service
            ;;
        stop)
            print_error "请使用 stop_service.sh脚停止服务"
            exit 1
            ;;
        restart)
            print_error "请使用 restart_service.sh脚重启服务"
            exit 1
            ;;
        status)
            print_error "请使用 status_service.sh脚本查看服务状态"
            exit 1
            ;;
        logs)
            print_error "请使用 logs_service.sh脚本查看日志"
            exit 1
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