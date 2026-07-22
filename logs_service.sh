#!/bin/bash

# ============================================
# Flask Web服务日志查看脚本
# 用于在Linux系统下查看Flask应用服务日志
# ============================================

# 设置脚本基本配置
set -e
set -u

#基本变量配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="tool_box_front"
LOG_DIR="$SCRIPT_DIR/logs"
ACCESS_LOG="$LOG_DIR/${APP_NAME}.log"
ERROR_LOG="$LOG_DIR/${APP_NAME}_error.log"

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

#显示访问日志
show_access_logs() {
    local lines=${1:-50}
    
    if [[ ! -f "$ACCESS_LOG" ]]; then
        print_error "访问日志文件不存在: $ACCESS_LOG"
        return 1
    fi
    
    print_info "显示最近 $lines行访问日志..."
    echo "========================================"
    tail -n "$lines" "$ACCESS_LOG"
    echo "========================================"
}

#显示错误日志
show_error_logs() {
    local lines=${1:-50}
    
    if [[ ! -f "$ERROR_LOG" ]]; then
        print_error "错误日志文件不存在: $ERROR_LOG"
        return 1
    fi
    
    print_info "显示最近 $lines行错误日志..."
    echo "========================================"
    tail -n "$lines" "$ERROR_LOG"
    echo "========================================"
}

#实时监控日志
follow_logs() {
    local log_type=${1:-all}
    
    if [[ ! -d "$LOG_DIR" ]]; then
        print_error "日志目录不存在: $LOG_DIR"
        return 1
    fi
    
    print_info "实时监控日志 (按 Ctrl+C停)..."
    echo "========================================"
    
    case "$log_type" in
        access)
            if [[ -f "$ACCESS_LOG" ]]; then
                tail -f "$ACCESS_LOG"
            else
                print_error "访问日志文件不存在: $ACCESS_LOG"
                return 1
            fi
            ;;
        error)
            if [[ -f "$ERROR_LOG" ]]; then
                tail -f "$ERROR_LOG"
            else
                print_error "错误日志文件不存在: $ERROR_LOG"
                return 1
            fi
            ;;
        all|*)
            if [[ -f "$ACCESS_LOG" && -f "$ERROR_LOG" ]]; then
                #同时监控两个日志文件
                (tail -f "$ACCESS_LOG" & tail -f "$ERROR_LOG") | head -n 100
                # 注意:这里的实现可能需要调整，实际使用中可能需要更复杂的处理
                print_info "建议分别监控两个日志文件"
                echo "访问日志: tail -f $ACCESS_LOG"
                echo "错误日志: tail -f $ERROR_LOG"
            elif [[ -f "$ACCESS_LOG" ]]; then
                tail -f "$ACCESS_LOG"
            elif [[ -f "$ERROR_LOG" ]]; then
                tail -f "$ERROR_LOG"
            else
                print_error "未找到任何日志文件"
                return 1
            fi
            ;;
    esac
}

#搜索日志内容
search_logs() {
    local keyword="$1"
    local log_type=${2:-all}
    local lines=${3:-100}
    
    if [[ -z "$keyword" ]]; then
        print_error "请提供搜索关键词"
        return 1
    fi
    
    print_info "搜索包含 '$keyword' 的日志内容..."
    echo "========================================"
    
    case "$log_type" in
        access)
            if [[ -f "$ACCESS_LOG" ]]; then
                grep -i "$keyword" "$ACCESS_LOG" | tail -n "$lines"
            else
                print_error "访问日志文件不存在"
            fi
            ;;
        error)
            if [[ -f "$ERROR_LOG" ]]; then
                grep -i "$keyword" "$ERROR_LOG" | tail -n "$lines"
            else
                print_error "错误日志文件不存在"
            fi
            ;;
        all|*)
            if [[ -f "$ACCESS_LOG" ]]; then
                echo "===访问日志中的匹配项 ==="
                grep -i "$keyword" "$ACCESS_LOG" | tail -n "$((lines/2))" 2>/dev/null || echo "未找到匹配项"
            fi
            if [[ -f "$ERROR_LOG" ]]; then
                echo "===错误日志中的匹配项 ==="
                grep -i "$keyword" "$ERROR_LOG" | tail -n "$((lines/2))" 2>/dev/null || echo "未找到匹配项"
            fi
            ;;
    esac
    echo "========================================"
}

#显示日志统计信息
show_log_stats() {
    print_info "日志统计信息..."
    echo "========================================"
    
    if [[ -d "$LOG_DIR" ]]; then
        echo "日志目录: $LOG_DIR"
        echo ""
        
        if [[ -f "$ACCESS_LOG" ]]; then
            local access_size=$(du -h "$ACCESS_LOG" 2>/dev/null | cut -f1)
            local access_lines=$(wc -l "$ACCESS_LOG" 2>/dev/null | cut -d' ' -f1)
            local access_last_mod=$(stat -c %y "$ACCESS_LOG" 2>/dev/null || stat -f %Sm "$ACCESS_LOG" 2>/dev/null)
            echo "访问日志:"
            echo "  文件大小: $access_size"
            echo " 行数: $access_lines"
            echo "  最后修改: $access_last_mod"
            echo ""
        fi
        
        if [[ -f "$ERROR_LOG" ]]; then
            local error_size=$(du -h "$ERROR_LOG" 2>/dev/null | cut -f1)
            local error_lines=$(wc -l "$ERROR_LOG" 2>/dev/null | cut -d' ' -f1)
            local error_last_mod=$(stat -c %y "$ERROR_LOG" 2>/dev/null || stat -f %Sm "$ERROR_LOG" 2>/dev/null)
            echo "错误日志:"
            echo "  文件大小: $error_size"
            echo " 行: $error_lines"
            echo "  最后修改: $error_last_mod"
            echo ""
        fi
        
        #统计错误日志中的错误类型
        if [[ -f "$ERROR_LOG" ]]; then
            echo "错误类型统计:"
            grep -i "error\|exception\|traceback" "$ERROR_LOG" 2>/dev/null | \
                grep -oE "(ERROR|Exception|Traceback)" 2>/dev/null | \
                sort | uniq -c | sort -nr | head -10 || echo "未找到错误信息"
        fi
    else
        print_error "日志目录不存在: $LOG_DIR"
    fi
    echo "========================================"
}

#显示使用帮助
show_help() {
    echo "用法: $0 [选项] [参数]"
    echo ""
    echo "选项:"
    echo "  access [行数]        查看访问日志 (默认50行)"
    echo "  error [行数]         查看错误日志 (默认50行)"
    echo "  follow [类型]        实时监控日志 (access/error/all)"
    echo "  search 关键词 [类型] [行数] 搜索日志内容"
    echo "  stats               显示日志统计信息"
    echo "  help                显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 access 100        # 查看最近100行访问日志"
    echo "  $0 error             # 查看最近50行错误日志"
    echo "  $0 follow access     # 实时监控访问日志"
    echo "  $0 search error      #搜索包含'error'的日志"
    echo "  $0 stats             #显示日志统计信息"
}

# 主程序入口
main() {
    case "${1:-help}" in
        access)
            show_access_logs "${2:-50}"
            ;;
        error)
            show_error_logs "${2:-50}"
            ;;
        follow)
            follow_logs "${2:-all}"
            ;;
        search)
            if [[ $# -lt 2 ]]; then
                print_error "请提供搜索关键词"
                show_help
                exit 1
            fi
            search_logs "$2" "${3:-all}" "${4:-100}"
            ;;
        stats)
            show_log_stats
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