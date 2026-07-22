#!/bin/bash

# ============================================
# 更新Token Manager JS文件到服务器脚本
# 将修改后的token-manager.js文件上传到服务器
# ============================================

# 设置脚本基本配置
set -e
set -u

# 默认变量配置
REMOTE_USER="root"
REMOTE_HOST="10.1.3.48"
REMOTE_PATH="/root/tool_box_front"
LOCAL_JS_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/static/js/token-manager.js"

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
    echo "  update-js <user@host>   更新token-manager.js文件到服务器"
    echo "  restart-service <user@host>  重启服务"
    echo "  deploy-all <user@host>   完整部署（更新+重启）"
    echo "  help                    显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 update-js root@10.1.3.48    # 更新JS文件"
    echo "  $0 deploy-all root@10.1.3.48   # 完整部署"
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

# 更新JS文件到服务器
update_js_file() {
    local ssh_target="$1"
    local host_ip="${ssh_target#*@}"
    
    print_info "更新token-manager.js文件到 $ssh_target..."
    
    # 检查本地文件是否存在
    if [[ ! -f "$LOCAL_JS_PATH" ]]; then
        print_error "本地JS文件不存在: $LOCAL_JS_PATH"
        return 1
    fi
    
    # 上传JS文件到服务器
    print_info "上传 token-manager.js 到服务器..."
    scp "$LOCAL_JS_PATH" "$ssh_target:$REMOTE_PATH/static/js/token-manager.js"
    
    print_info "设置文件权限..."
    ssh "$ssh_target" "
        chmod 644 $REMOTE_PATH/static/js/token-manager.js
        echo 'JS文件已更新'
    "
    
    print_success "token-manager.js文件已成功上传到服务器"
}

# 重启服务
restart_service() {
    local ssh_target="$1"
    
    print_info "重启服务..."
    
    ssh "$ssh_target" "
        cd $REMOTE_PATH
        
        echo '停止服务...'
        ./stop_service.sh stop 2>/dev/null || true
        
        # 等待服务完全停止
        sleep 3
        
        echo '启动服务...'
        ./start_service.sh start
        
        # 等待服务启动
        sleep 5
        
        echo '检查服务状态...'
        ./status_service.sh status
    "
    
    print_success "服务已重启"
}

# 完整部署流程
deploy_all() {
    local ssh_target="$1"
    
    print_info "开始完整部署流程..."
    
    # 检查SSH连接
    if ! check_ssh_connection "$ssh_target"; then
        return 1
    fi
    
    # 更新JS文件
    update_js_file "$ssh_target"
    
    # 重启服务
    restart_service "$ssh_target"
    
    print_success "完整部署完成！"
    echo ""
    echo "========================================"
    echo "现在JavaScript文件将使用POST方法请求token"
    echo "受影响的页面包括："
    echo "- http://$ssh_target:5000/user_duration"
    echo "- http://$ssh_target:5000/user_register"
    echo "========================================"
}

# 主程序入口
main() {
    case "${1:-help}" in
        update-js)
            if [[ $# -ne 2 ]]; then
                print_error "请提供服务器地址，例如: $0 update-js user@10.1.3.48"
                exit 1
            fi
            
            local ssh_target="$2"
            
            # 检查SSH连接
            if ! check_ssh_connection "$ssh_target"; then
                exit 1
            fi
            
            update_js_file "$ssh_target"
            ;;
            
        restart-service)
            if [[ $# -ne 2 ]]; then
                print_error "请提供服务器地址，例如: $0 restart-service user@10.1.3.48"
                exit 1
            fi
            
            local ssh_target="$2"
            
            # 检查SSH连接
            if ! check_ssh_connection "$ssh_target"; then
                exit 1
            fi
            
            restart_service "$ssh_target"
            ;;
            
        deploy-all)
            if [[ $# -ne 2 ]]; then
                print_error "请提供服务器地址，例如: $0 deploy-all user@10.1.3.48"
                exit 1
            fi
            
            deploy_all "$2"
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