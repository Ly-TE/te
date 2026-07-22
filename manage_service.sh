#!/bin/bash

# ============================================
# Flask Web服务一键管理脚本
#集成启动、停止、重启、状态查看等功能
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

#显示菜单
show_menu() {
    clear
    echo "========================================"
    echo "     $APP_NAME 服务管理工具"
    echo "========================================"
    echo "1.启动服务"
    echo "2.停服务止服务"
    echo "3. 重启服务"
    echo "4. 查看服务状态"
    echo "5. 查看访问日志"
    echo "6. 查看错误日志"
    echo "7. 实时监控日志"
    echo "8. 查看日志统计"
    echo "9. 搜索日志"
    echo "0. 退出"
    echo "========================================"
    echo ""
}

#获取用户选择
get_user_choice() {
    read -p "请选择操作 [0-9]: " choice
    echo "$choice"
}

#主循环
main_loop() {
    while true; do
        show_menu
        choice=$(get_user_choice)
        
        case "$choice" in
            1)
                print_info "正在启动服务..."
                "$SCRIPT_DIR/start_service.sh" start
                echo ""
                read -p "按回车键继续..."
                ;;
            2)
                print_info "正在停止服务..."
                "$SCRIPT_DIR/stop_service.sh" stop
                echo ""
                read -p "按回车键继续..."
                ;;
            3)
                print_info "正在重启服务..."
                "$SCRIPT_DIR/restart_service.sh" restart
                echo ""
                read -p "按回车键继续..."
                ;;
            4)
                "$SCRIPT_DIR/status_service.sh" status
                echo ""
                read -p "按回车键继续..."
                ;;
            5)
                echo ""
                read -p "显示行数 (默认50): " lines
                lines=${lines:-50}
                "$SCRIPT_DIR/logs_service.sh" access "$lines"
                echo ""
                read -p "按回车键继续..."
                ;;
            6)
                echo ""
                read -p "显示行数 (默认50): " lines
                lines=${lines:-50}
                "$SCRIPT_DIR/logs_service.sh" error "$lines"
                echo ""
                read -p "按回车键继续..."
                ;;
            7)
                echo ""
                echo "选择监控类型:"
                echo "1.访日志"
                echo "2.错日志"
                echo "3.所有日志"
                read -p "请选择 [1-3]: " log_choice
                
                case "$log_choice" in
                    1) log_type="access" ;;
                    2) log_type="error" ;;
                    3) log_type="all" ;;
                    *) log_type="all" ;;
                esac
                
                print_info "按 Ctrl+C停监控"
                "$SCRIPT_DIR/logs_service.sh" follow "$log_type"
                echo ""
                read -p "按回车键继续..."
                ;;
            8)
                "$SCRIPT_DIR/logs_service.sh" stats
                echo ""
                read -p "按回车键继续..."
                ;;
            9)
                echo ""
                read -p "输入搜索关键词: " keyword
                if [[ -n "$keyword" ]]; then
                    echo "选择搜索范围:"
                    echo "1.访问日志"
                    echo "2.错误日志"
                    echo "3.所有日志"
                    read -p "请选择 [1-3]: " search_choice
                    
                    case "$search_choice" in
                        1) search_type="access" ;;
                        2) search_type="error" ;;
                        3) search_type="all" ;;
                        *) search_type="all" ;;
                    esac
                    
                    read -p "显示行数 (默认100): " search_lines
                    search_lines=${search_lines:-100}
                    
                    "$SCRIPT_DIR/logs_service.sh" search "$keyword" "$search_type" "$search_lines"
                else
                    print_error "关键词不能为空"
                fi
                echo ""
                read -p "按回车键继续..."
                ;;
            0)
                print_info "退出服务管理工具"
                exit 0
                ;;
            *)
                print_error "无效选择，请重新输入"
                sleep 1
                ;;
        esac
    done
}

#显示使用帮助
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  menu    显示交互式菜单 (默认)"
    echo "  start    启动服务"
    echo "  stop    停止服务"
    echo "  restart  重启服务"
    echo "  status   查看服务状态"
    echo "  logs     查看日志相关选项"
    echo "  help    显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0           #显示交互式菜单"
    echo "  $0 start     #启动服务"
    echo "  $0 status    # 查看服务状态"
    echo "  $0 logs      # 显示日志操作选项"
}

# 主程序入口
main() {
    case "${1:-menu}" in
        menu)
            main_loop
            ;;
        start)
            "$SCRIPT_DIR/start_service.sh" start
            ;;
        stop)
            "$SCRIPT_DIR/stop_service.sh" stop
            ;;
        restart)
            "$SCRIPT_DIR/restart_service.sh" restart
            ;;
        status)
            "$SCRIPT_DIR/status_service.sh" status
            ;;
        logs)
            echo "日志操作选项:"
            echo "  $0 logs access [行数]     # 查看访问日志"
            echo "  $0 logs error [行数]      # 查看错误日志"
            echo "  $0 logs follow [类型]     # 实时监控日志"
            echo "  $0 logs search 关键词     # 搜索日志"
            echo "  $0 logs stats             # 查看日志统计"
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