#!/bin/bash

# ============================================
# 服务连接诊断脚本
# 用于诊断Flask服务连接问题
# ============================================

# 设置脚本基本配置
set -e
set -u

# 默认变量配置
REMOTE_USER="root"
REMOTE_HOST="192.168.3.101"
REMOTE_PATH="/root/tool_box_front"
LOCAL_PROJECT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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
    echo "  diagnose <user@host>  诊断服务连接问题"
    echo "  check-service <user@host>  检查服务状态"
    echo "  check-firewall <user@host>  检查防火墙配置"
    echo "  check-network <user@host>  检查网络连接"
    echo "  fix-all <user@host>     修复所有常见问题"
    echo "  help                   显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 diagnose root@192.168.3.101    # 诊断连接问题"
    echo "  $0 check-service root@192.168.3.101  # 检查服务状态"
}

# 检查SSH连接
check_ssh_connection() {
    local ssh_target="$1"
    
    print_info "检查SSH连接到 $ssh_target..."
    
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$ssh_target" exit 2>/dev/null; then
        print_success "SSH连接正常"
        return 0
    else
        print_error "无法连接到 $ssh_target，请检查网络连接和SSH配置"
        return 1
    fi
}

# 检查服务状态
check_service_status() {
    local ssh_target="$1"
    
    print_info "检查服务状态..."
    
    ssh "$ssh_target" "
        cd $REMOTE_PATH
        
        # 检查服务是否运行
        if ./status_service.sh status 2>/dev/null; then
            echo ''
            print_success '服务正在运行'
        else
            print_error '服务未运行'
        fi
        
        # 检查进程
        echo ''
        echo '=== 进程检查 ==='
        ps aux | grep -i 'python.*app\.py\|gunicorn' | grep -v grep || echo '未找到相关进程'
        
        # 检查端口占用
        echo ''
        echo '=== 端口检查 ==='
        if command -v netstat >/dev/null 2>&1; then
            netstat -tlnp | grep :5000 || echo '端口5000未被占用'
        elif command -v ss >/dev/null 2>&1; then
            ss -tlnp | grep :5000 || echo '端口5000未被占用'
        else
            lsof -i :5000 || echo '未找到端口占用信息'
        fi
    "
}

# 检查防火墙配置
check_firewall_config() {
    local ssh_target="$1"
    
    print_info "检查防火墙配置..."
    
    ssh "$ssh_target" "
        echo '=== 防火墙状态 ==='
        if systemctl is-active --quiet firewalld 2>/dev/null; then
            echo 'Firewalld 正在运行'
            firewall-cmd --list-ports 2>/dev/null || echo '无法获取firewalld端口信息'
        elif systemctl is-active --quiet iptables 2>/dev/null; then
            echo 'iptables 正在运行'
            iptables -L -n | grep 5000 || echo '未找到端口5000相关规则'
        else
            echo '防火墙可能未运行'
        fi
        
        echo ''
        echo '=== 网络监听 ==='
        ss -tlnp | grep :5000 || netstat -tlnp | grep :5000 || echo '端口5000未监听'
    "
}

# 检查网络连接
check_network_connectivity() {
    local ssh_target="$1"
    local host_ip="${ssh_target#*@}"
    
    print_info "检查网络连接..."
    
    # 检查本地端口
    ssh "$ssh_target" "
        echo '=== 本地连接测试 ==='
        curl -I localhost:5000 2>/dev/null || echo '无法连接到本地5000端口'
        
        echo ''
        echo '=== 服务绑定检查 ==='
        ss -tlnp | grep ':5000' || netstat -tlnp | grep ':5000'
    "
    
    # 检查从本地到服务器的连接
    print_info "从本地测试连接到服务器..."
    if nc -z -w5 "$host_ip" 5000 2>/dev/null; then
        print_success "可以连接到 $host_ip:5000"
    else
        print_error "无法连接到 $host_ip:5000，请检查防火墙设置"
    fi
}

# 修复服务
fix_service() {
    local ssh_target="$1"
    
    print_info "修复服务..."
    
    ssh "$ssh_target" "
        cd $REMOTE_PATH
        
        # 停止现有服务
        ./stop_service.sh stop 2>/dev/null || true
        
        # 等待几秒
        sleep 3
        
        # 确保端口已释放
        lsof -i :5000 | grep LISTEN | awk '{print \$2}' | xargs kill -9 2>/dev/null || true
        
        # 启动服务
        ./start_service.sh start
        
        # 等待服务启动
        sleep 5
        
        # 检查服务状态
        ./status_service.sh status
    "
}

# 修复防火墙
fix_firewall() {
    local ssh_target="$1"
    
    print_info "修复防火墙配置..."
    
    ssh "$ssh_target" "
        # 检查并配置防火墙
        if systemctl is-active --quiet firewalld 2>/dev/null; then
            print_info '配置firewalld...'
            firewall-cmd --permanent --add-port=5000/tcp 2>/dev/null || true
            firewall-cmd --reload 2>/dev/null || true
            print_success 'firewalld配置完成'
        elif command -v iptables >/dev/null 2>&1; then
            print_info '配置iptables...'
            iptables -A INPUT -p tcp --dport 5000 -j ACCEPT 2>/dev/null || true
            print_success 'iptables规则添加完成'
        else
            print_warn '未找到可用的防火墙工具'
        fi
    "
}

# 诊断完整问题
diagnose_issues() {
    local ssh_target="$1"
    
    print_info "开始诊断服务连接问题..."
    
    # 检查SSH连接
    if ! check_ssh_connection "$ssh_target"; then
        return 1
    fi
    
    print_info "=== 1. 检查服务状态 ==="
    check_service_status "$ssh_target"
    
    print_info ""
    print_info "=== 2. 检查防火墙配置 ==="
    check_firewall_config "$ssh_target"
    
    print_info ""
    print_info "=== 3. 检查网络连接 ==="
    check_network_connectivity "$ssh_target"
    
    print_info ""
    print_success "诊断完成！请根据上述信息排查问题"
}

# 完整修复流程
fix_all_issues() {
    local ssh_target="$1"
    
    print_info "开始完整修复流程..."
    
    # 检查SSH连接
    if ! check_ssh_connection "$ssh_target"; then
        return 1
    fi
    
    # 修复服务
    fix_service "$ssh_target"
    
    # 修复防火墙
    fix_firewall "$ssh_target"
    
    print_success "修复完成！服务应该可以访问了"
    echo ""
    echo "========================================"
    echo "请稍等几分钟让服务完全启动"
    echo "然后访问: http://$ssh_target:5000"
    echo "========================================"
}

# 主程序入口
main() {
    case "${1:-help}" in
        diagnose)
            if [[ $# -ne 2 ]]; then
                print_error "请提供服务器地址，例如: $0 diagnose user@192.168.3.101"
                exit 1
            fi
            
            diagnose_issues "$2"
            ;;
            
        check-service)
            if [[ $# -ne 2 ]]; then
                print_error "请提供服务器地址，例如: $0 check-service user@192.168.3.101"
                exit 1
            fi
            
            local ssh_target="$2"
            
            # 检查SSH连接
            if ! check_ssh_connection "$ssh_target"; then
                exit 1
            fi
            
            check_service_status "$ssh_target"
            ;;
            
        check-firewall)
            if [[ $# -ne 2 ]]; then
                print_error "请提供服务器地址，例如: $0 check-firewall user@192.168.3.101"
                exit 1
            fi
            
            local ssh_target="$2"
            
            # 检查SSH连接
            if ! check_ssh_connection "$ssh_target"; then
                exit 1
            fi
            
            check_firewall_config "$ssh_target"
            ;;
            
        check-network)
            if [[ $# -ne 2 ]]; then
                print_error "请提供服务器地址，例如: $0 check-network user@192.168.3.101"
                exit 1
            fi
            
            local ssh_target="$2"
            
            # 检查SSH连接
            if ! check_ssh_connection "$ssh_target"; then
                exit 1
            fi
            
            check_network_connectivity "$ssh_target"
            ;;
            
        fix-all)
            if [[ $# -ne 2 ]]; then
                print_error "请提供服务器地址，例如: $0 fix-all user@192.168.3.101"
                exit 1
            fi
            
            fix_all_issues "$2"
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