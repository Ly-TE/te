#!/bin/bash

# ============================================
# Flask Web服务状态查看脚本
# 用于在Linux系统下查看Flask应用服务状态
# ============================================

# 设置脚本基本配置
set -e
set -u

#基本变量配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="tool_box_front"
PID_FILE="$SCRIPT_DIR/${APP_NAME}.pid"
LOG_DIR="$SCRIPT_DIR/logs"

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

#检查服务状态
check_status() {
    print_info "检查 $APP_NAME 服务状态..."
    echo "========================================"
    
    #检查PID文件
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        echo "PID文件: $PID_FILE"
        echo "PID: $pid"
        
        #检查进程是否存在
        if ps -p "$pid" > /dev/null 2>&1; then
            print_success "服务正在运行"
            
            #获取进程详细信息
            echo "进程信息:"
            ps -p "$pid" -o pid,ppid,cmd,etime,pcpu,pmem --no-headers
            
            #检查端口占用
            echo ""
            echo "端口占用情况:"
            if command -v netstat &> /dev/null; then
                netstat -tlnp | grep ":5000" | head -5
            elif command -v ss &> /dev/null; then
                ss -tlnp | grep ":5000" | head -5
            else
                echo "无法检查端口占用情况 (缺少netstat或ss命令)"
            fi
        else
            print_error "服务未运行 (PID文件存在但进程不存在)"
            print_warn "建议清理PID文件: rm $PID_FILE"
        fi
    else
        print_warn "服务未运行 (未找到PID文件)"
    fi
    
    #检查日志文件
    echo ""
    echo "日志文件状态:"
    if [[ -d "$LOG_DIR" ]]; then
        echo "日志目录: $LOG_DIR"
        if [[ -f "$LOG_DIR/${APP_NAME}.log" ]]; then
            local log_size=$(du -h "$LOG_DIR/${APP_NAME}.log" 2>/dev/null | cut -f1)
            local log_lines=$(wc -l "$LOG_DIR/${APP_NAME}.log" 2>/dev/null | cut -d' ' -f1)
            echo "访问日志: ${log_size} (${log_lines}行)"
        fi
        if [[ -f "$LOG_DIR/${APP_NAME}_error.log" ]]; then
            local error_size=$(du -h "$LOG_DIR/${APP_NAME}_error.log" 2>/dev/null | cut -f1)
            local error_lines=$(wc -l "$LOG_DIR/${APP_NAME}_error.log" 2>/dev/null | cut -d' ' -f1)
            echo "错误日志: ${error_size} (${error_lines}行)"
        fi
    else
        echo "日志目录不存在: $LOG_DIR"
    fi
    
    #检查依赖环境
    echo ""
    echo "环境检查:"
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 --version 2>&1)
        print_success "Python: $python_version"
    else
        print_error "Python3 未安装"
    fi
    
    if [[ -d "$SCRIPT_DIR/venv" ]]; then
        print_success "虚拟环境存在"
    else
        print_warn "虚拟环境不存在"
    fi
    
    if [[ -f "$SCRIPT_DIR/.env" ]]; then
        print_success "配置文件存在"
    else
        print_warn "配置文件不存在"
    fi
    
    echo "========================================"
}

#显示使用帮助
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  status   查看服务状态"
    echo "  help     显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 status    # 查看服务状态"
}

# 主程序入口
main() {
    case "${1:-help}" in
        status)
            check_status
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