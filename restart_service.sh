#!/bin/bash

# ============================================
# Flask Web服务重启脚本
# 用于在Linux系统下重启Flask应用服务
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

#重启服务函数
restart_service() {
    print_info "正在重启 $APP_NAME 服务..."
    
    #停止服务
    "$SCRIPT_DIR/stop_service.sh" stop
    
    #等待服务完全停止
    sleep 2
    
    #启动服务
    "$SCRIPT_DIR/start_service.sh" start
}

#显示使用帮助
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  restart  重启服务"
    echo "  help     显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 restart   # 重启服务"
}

# 主程序入口
main() {
    case "${1:-help}" in
        restart)
            restart_service
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