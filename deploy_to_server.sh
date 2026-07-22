#!/bin/bash

# ============================================
# 远程服务器部署脚本
# 用于将tool_box_front应用部署到远程服务器
# ============================================

# 设置脚本基本配置
set -e
set -u

# 默认变量配置
REMOTE_USER="username"
REMOTE_HOST="192.168.3.101"
REMOTE_PATH="/home/$REMOTE_USER/tool_box_front"
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
    echo "  deploy <user@host>  部署到指定服务器 (例如: deploy user@192.168.3.101)"
    echo "  upload <user@host>  仅上传代码到指定服务器"
    echo "  setup <user@host>   仅在服务器上设置环境"
    echo "  help               显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 deploy username@192.168.3.101    # 完整部署"
    echo "  $0 upload username@192.168.3.101    # 仅上传代码"
    echo "  $0 setup username@192.168.3.101     # 仅设置环境"
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

# 上传代码到服务器
upload_code() {
    local ssh_target="$1"
    
    print_info "开始上传代码到 $ssh_target..."
    
    # 创建临时压缩包
    local temp_archive="/tmp/tool_box_front_$(date +%s).tar.gz"
    print_info "创建项目压缩包..."
    tar -czf "$temp_archive" -C "$(dirname "$LOCAL_PROJECT_PATH")" "$(basename "$LOCAL_PROJECT_PATH")"
    
    # 上传压缩包到服务器
    print_info "上传压缩包到服务器..."
    scp "$temp_archive" "$ssh_target:/tmp/"
    
    # 在服务器上解压
    print_info "在服务器上解压代码..."
    ssh "$ssh_target" "
        mkdir -p $REMOTE_PATH
        tar -xzf /tmp/$(basename "$temp_archive") -C /home/$(echo "$ssh_target" | cut -d@ -f1)/
        rm -f /tmp/$(basename "$temp_archive")
    "
    
    # 清理本地临时文件
    rm -f "$temp_archive"
    
    print_success "代码上传完成"
}

# 在服务器上设置环境
setup_environment() {
    local ssh_target="$1"
    
    print_info "在服务器上设置运行环境..."
    
    ssh "$ssh_target" "
        cd $REMOTE_PATH
        
        # 设置脚本执行权限
        chmod +x *.sh
        
        # 运行安装脚本
        ./install_service.sh
        
        # 提示用户配置环境变量
        if [ ! -f .env ]; then
            echo '警告: 未找到 .env 配置文件，请手动创建并配置数据库等参数'
            echo '可以复制 .env.example 并进行修改'
        fi
    "
    
    print_success "环境设置完成"
}

# 完整部署流程
full_deploy() {
    local ssh_target="$1"
    
    print_info "开始完整部署到 $ssh_target..."
    
    # 检查SSH连接
    if ! check_ssh_connection "$ssh_target"; then
        return 1
    fi
    
    # 上传代码
    upload_code "$ssh_target"
    
    # 设置环境
    setup_environment "$ssh_target"
    
    print_success "部署完成！"
    echo ""
    echo "========================================"
    echo "下一步操作："
    echo "1. SSH到服务器: ssh $ssh_target"
    echo "2. 进入项目目录: cd $REMOTE_PATH"
    echo "3. 配置环境变量: nano .env"
    echo "4. 启动服务: ./start_service.sh start"
    echo "========================================"
}

# 主程序入口
main() {
    case "${1:-help}" in
        deploy)
            if [[ $# -ne 2 ]]; then
                print_error "请提供服务器地址，例如: $0 deploy user@192.168.3.101"
                exit 1
            fi
            
            full_deploy "$2"
            ;;
            
        upload)
            if [[ $# -ne 2 ]]; then
                print_error "请提供服务器地址，例如: $0 upload user@192.168.3.101"
                exit 1
            fi
            
            local ssh_target="$2"
            
            # 检查SSH连接
            if ! check_ssh_connection "$ssh_target"; then
                exit 1
            fi
            
            upload_code "$ssh_target"
            ;;
            
        setup)
            if [[ $# -ne 2 ]]; then
                print_error "请提供服务器地址，例如: $0 setup user@192.168.3.101"
                exit 1
            fi
            
            local ssh_target="$2"
            
            # 检查SSH连接
            if ! check_ssh_connection "$ssh_target"; then
                exit 1
            fi
            
            setup_environment "$ssh_target"
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