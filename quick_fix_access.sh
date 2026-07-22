#!/bin/bash

# ============================================
# 快速修复服务访问问题脚本
# 一键解决服务无法访问的常见问题
# ============================================

# 设置脚本基本配置
set -e
set -u

# 默认变量配置
REMOTE_USER="root"
REMOTE_HOST="192.168.3.101"
REMOTE_PATH="/root/tool_box_front"

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

# 显示使用帮助
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  quick-fix <user@host>  快速修复服务访问问题"
    echo "  help                  显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 quick-fix root@192.168.3.101    # 快速修复访问问题"
}

# 快速修复服务访问问题
quick_fix_access_issue() {
    local ssh_target="$1"
    local host_ip="${ssh_target#*@}"
    
    print_info "开始快速修复服务访问问题..."
    print_info "目标服务器: $ssh_target"
    
    # 检查SSH连接
    print_info "检查SSH连接..."
    if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "$ssh_target" exit 2>/dev/null; then
        print_error "无法连接到 $ssh_target，请检查网络连接和SSH配置"
        return 1
    fi
    print_success "SSH连接正常"
    
    print_info "开始修复流程..."
    
    ssh "$ssh_target" "
        cd $REMOTE_PATH
        
        echo '--- 1. 停止现有服务 ---'
        ./stop_service.sh stop 2>/dev/null || true
        sleep 3
        
        echo '--- 2. 清理残留进程 ---'
        pids=(\$(ps aux | grep -i 'python.*app\.py\|gunicorn' | grep -v grep | awk '{print \$2}'))
        if [ \${#pids[@]} -gt 0 ]; then
            echo \"终止残留进程: \${pids[*]}\"
            kill -9 \${pids[*]} 2>/dev/null || true
        else
            echo '未发现残留进程'
        fi
        
        sleep 3
        
        echo '--- 3. 检查端口是否已释放 ---'
        if netstat -tlnp 2>/dev/null | grep :5000 >/dev/null; then
            echo '警告: 端口5000仍然被占用'
        else
            echo '端口5000已释放'
        fi
        
        echo '--- 4. 检查防火墙配置 ---'
        if systemctl is-active --quiet firewalld 2>/dev/null; then
            echo '配置firewalld防火墙...'
            firewall-cmd --permanent --add-port=5000/tcp 2>/dev/null || echo '添加端口规则失败'
            firewall-cmd --reload 2>/dev/null || echo '重载防火墙配置失败'
            firewall-cmd --list-ports 2>/dev/null | grep 5000 >/dev/null && echo '端口5000已开放' || echo '端口5000可能未开放'
        elif command -v iptables >/dev/null 2>&1; then
            echo '配置iptables防火墙...'
            iptables -I INPUT -p tcp --dport 5000 -j ACCEPT 2>/dev/null || echo '添加iptables规则失败'
            iptables -L -n | grep 'dpt:5000' >/dev/null && echo 'iptables规则已添加' || echo 'iptables规则可能未添加'
        else
            echo '未找到标准防火墙工具'
        fi
        
        echo '--- 5. 启动服务 ---'
        ./start_service.sh start
        
        echo '--- 6. 等待服务启动 ---'
        sleep 8
        
        echo '--- 7. 检查服务状态 ---'
        ./status_service.sh status || echo '服务状态检查失败'
        
        echo '--- 8. 检查端口监听 ---'
        if command -v netstat >/dev/null 2>&1; then
            netstat -tlnp | grep :5000 || echo '端口5000未监听'
        elif command -v ss >/dev/null 2>&1; then
            ss -tlnp | grep :5000 || echo '端口5000未监听'
        else
            lsof -i :5000 || echo '无法检查端口监听状态'
        fi
        
        echo '--- 9. 测试本地连接 ---'
        timeout 5 curl -I localhost:5000 2>/dev/null | head -1 || echo '本地连接测试失败'
    "
    
    print_info ""
    print_success "快速修复完成！"
    echo ""
    echo "========================================"
    echo "请稍等1-2分钟让服务完全启动"
    echo "然后尝试访问: http://$host_ip:5000"
    echo ""
    echo "如果仍然无法访问，请运行以下命令进一步诊断："
    echo "./diagnose_connection.sh diagnose $ssh_target"
    echo "========================================"
}

# 主程序入口
main() {
    case "${1:-help}" in
        quick-fix)
            if [[ $# -ne 2 ]]; then
                print_error "请提供服务器地址，例如: $0 quick-fix user@192.168.3.101"
                exit 1
            fi
            
            quick_fix_access_issue "$2"
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