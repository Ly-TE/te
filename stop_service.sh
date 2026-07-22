#!/bin/bash

# ============================================
# Flask Web服务停止脚本
# 用于在Linux系统下停止Flask应用服务
# ============================================

# 设置脚本基本配置
set -e
set -u

#基本变量配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="tool_box_front"
PID_FILE="$SCRIPT_DIR/${APP_NAME}.pid"

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

#检查服务是否运行
is_running() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

#停止服务函数
stop_service() {
    if ! is_running; then
        print_warn "服务未在运行"
        return 0
    fi
    
    local pid=$(cat "$PID_FILE")
    print_info "正在停止 $APP_NAME 服务 (PID: $pid)..."
    
    # 优雅停止服务
    if kill -TERM "$pid" 2>/dev/null; then
        #等待服务优雅关闭
        local count=0
        while [[ $count -lt 30 ]] && ps -p "$pid" > /dev/null 2>&1; do
            sleep 1
            ((count++))
        done
        
        # 如果服务仍未停止，强制杀死
        if ps -p "$pid" > /dev/null 2>&1; then
            print_warn "服务未正常关闭，正在强制停止..."
            kill -KILL "$pid" 2>/dev/null || true
            sleep 2
        fi
    fi
    
    #清理PID文件
    rm -f "$PID_FILE"
    
    # 最终检查
    if ps -p "$pid" > /dev/null 2>&1; then
        print_error "服务停止失败"
        exit 1
    else
        print_success "$APP_NAME 服务已停止"
    fi
}

#显示使用帮助
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  stop    停止服务"
    echo "  help    显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 stop      #停服务止服务"
}

# 主程序入口
main() {
    case "${1:-help}" in
        stop)
            stop_service
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