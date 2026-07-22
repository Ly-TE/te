#!/bin/bash

# ============================================
# 生产环境修复部署脚本
# 解决urllib3与OpenSSL兼容性问题
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
    echo "  fix-openssl <user@host>  修复OpenSSL兼容性问题"
    echo "  update-deps <user@host>   更新服务器依赖"
    echo "  restart-service <user@host>  重启服务"
    echo "  full-fix <user@host>     完整修复流程"
    echo "  help                    显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 fix-openssl root@192.168.3.101    # 修复OpenSSL兼容性"
    echo "  $0 full-fix root@192.168.3.101       # 完整修复流程"
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

# 修复OpenSSL兼容性问题
fix_openssl_compatibility() {
    local ssh_target="$1"
    
    print_info "修复OpenSSL兼容性问题..."
    
    ssh "$ssh_target" "
        cd $REMOTE_PATH
        
        # 激活虚拟环境
        source venv/bin/activate
        
        # 降级urllib3到兼容版本
        print_info '正在降级urllib3...'
        pip install 'urllib3<2.0.0' --force-reinstall
        
        # 确保requirements.txt也更新
        if grep -q 'urllib3==' requirements.txt; then
            sed -i 's/urllib3==.*/urllib3<2.0.0  # 修复与旧版OpenSSL的兼容性问题/' requirements.txt
        elif ! grep -q 'urllib3<' requirements.txt; then
            echo '' >> requirements.txt
            echo '# 兼容性修复' >> requirements.txt
            echo 'urllib3<2.0.0  # 修复与旧版OpenSSL的兼容性问题' >> requirements.txt
        fi
        
        print_success 'OpenSSL兼容性修复完成'
    "
    
    print_success "OpenSSL兼容性问题修复完成！"
}

# 更新服务器依赖
update_dependencies() {
    local ssh_target="$1"
    
    print_info "更新服务器依赖..."
    
    ssh "$ssh_target" "
        cd $REMOTE_PATH
        
        # 激活虚拟环境
        source venv/bin/activate
        
        # 重新安装依赖（会应用新的urllib3版本约束）
        pip install -r requirements.txt --force-reinstall
        
        print_success '依赖更新完成'
    "
    
    print_success "服务器依赖更新完成！"
}

# 重启服务
restart_service() {
    local ssh_target="$1"
    
    print_info "重启服务..."
    
    ssh "$ssh_target" "
        cd $REMOTE_PATH
        
        # 停止服务
        ./stop_service.sh stop
        
        # 等待几秒确保服务完全停止
        sleep 3
        
        # 启动服务
        ./start_service.sh start
        
        # 等待服务启动
        sleep 5
        
        # 检查服务状态
        ./status_service.sh status
    "
    
    print_success "服务已重启！"
}

# 完整修复流程
full_fix_process() {
    local ssh_target="$1"
    
    print_info "开始完整修复流程..."
    
    # 检查SSH连接
    if ! check_ssh_connection "$ssh_target"; then
        return 1
    fi
    
    # 修复OpenSSL兼容性
    fix_openssl_compatibility "$ssh_target"
    
    # 更新依赖
    update_dependencies "$ssh_target"
    
    # 重启服务
    restart_service "$ssh_target"
    
    print_success "完整修复流程完成！"
    echo ""
    echo "========================================"
    echo "服务现在应该可以正常运行，不再有OpenSSL兼容性警告"
    echo "访问地址: http://$ssh_target:5000"
    echo "========================================"
}

# 主程序入口
main() {
    case "${1:-help}" in
        fix-openssl)
            if [[ $# -ne 2 ]]; then
                print_error "请提供服务器地址，例如: $0 fix-openssl user@192.168.3.101"
                exit 1
            fi
            
            local ssh_target="$2"
            
            # 检查SSH连接
            if ! check_ssh_connection "$ssh_target"; then
                exit 1
            fi
            
            fix_openssl_compatibility "$ssh_target"
            ;;
            
        update-deps)
            if [[ $# -ne 2 ]]; then
                print_error "请提供服务器地址，例如: $0 update-deps user@192.168.3.101"
                exit 1
            fi
            
            local ssh_target="$2"
            
            # 检查SSH连接
            if ! check_ssh_connection "$ssh_target"; then
                exit 1
            fi
            
            update_dependencies "$ssh_target"
            ;;
            
        restart-service)
            if [[ $# -ne 2 ]]; then
                print_error "请提供服务器地址，例如: $0 restart-service user@192.168.3.101"
                exit 1
            fi
            
            local ssh_target="$2"
            
            # 检查SSH连接
            if ! check_ssh_connection "$ssh_target"; then
                exit 1
            fi
            
            restart_service "$ssh_target"
            ;;
            
        full-fix)
            if [[ $# -ne 2 ]]; then
                print_error "请提供服务器地址，例如: $0 full-fix user@192.168.3.101"
                exit 1
            fi
            
            full_fix_process "$2"
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