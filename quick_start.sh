#!/bin/bash

# ============================================
#快速开始脚本
# 一键安装和启动Flask Web服务
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

#检查是否在Linux环境
check_environment() {
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        print_error "此脚本需要在Linux环境下运行"
        print_info "请在Linux服务器或WSL中执行"
        exit 1
    fi
}

#设置脚本权限
set_permissions() {
    print_info "设置脚本执行权限..."
    
    chmod +x "$SCRIPT_DIR"/*.sh 2>/dev/null || true
    print_success "脚本权限设置完成"
}

#快速安装
quick_install() {
    print_info "开始快速安装..."
    
    #运行安装脚本
    if [[ -f "$SCRIPT_DIR/install_service.sh" ]]; then
        "$SCRIPT_DIR/install_service.sh" install
    else
        print_error "安装脚本不存在: install_service.sh"
        exit 1
    fi
}

#配置检查
check_configuration() {
    print_info "检查配置文件..."
    
    local env_file="$SCRIPT_DIR/.env"
    
    if [[ ! -f "$env_file" ]]; then
        print_error "配置文件不存在: $env_file"
        print_info "请先运行安装脚本创建配置文件"
        return 1
    fi
    
    #检查关键配置项
    local missing_configs=()
    
    if ! grep -q "DB_HOST" "$env_file" 2>/dev/null; then
        missing_configs+=("DB_HOST")
    fi
    
    if ! grep -q "DB_USER" "$env_file" 2>/dev/null; then
        missing_configs+=("DB_USER")
    fi
    
    if [[ ${#missing_configs[@]} -gt 0 ]]; then
        print_warn "配置文件缺少以下项: ${missing_configs[*]}"
        print_info "请编辑 $env_file 文件完善配置"
        return 1
    fi
    
    print_success "配置文件检查通过"
    return 0
}

#启动服务
start_service() {
    print_info "启动服务..."
    
    if [[ -f "$SCRIPT_DIR/start_service.sh" ]]; then
        "$SCRIPT_DIR/start_service.sh" start
    else
        print_error "启动脚本不存在: start_service.sh"
        exit 1
    fi
}

#显示访问信息
show_access_info() {
    print_success "服务启动完成！"
    echo ""
    echo "========================================"
    echo "访问信息:"
    echo "  本地访问: http://localhost:5000"
    echo " 外访问: http://$(hostname -I | awk '{print $1}'):5000"
    echo ""
    echo "管理命令:"
    echo "  查看状态: $SCRIPT_DIR/status_service.sh status"
    echo " 停服务止服务: $SCRIPT_DIR/stop_service.sh stop"
    echo "  重启服务: $SCRIPT_DIR/restart_service.sh restart"
    echo "  查看日志: $SCRIPT_DIR/logs_service.sh"
    echo " 管界面: $SCRIPT_DIR/manage_service.sh"
    echo "========================================"
}

#显示使用帮助
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  install   完整安装并启动服务 (默认)"
    echo "  setup      仅安装环境"
    echo "  start      仅启动服务"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 install   # 一键安装并启动"
    echo "  $0 setup     # 仅安装环境"
    echo "  $0 start     # 仅启动服务"
}

# 主程序入口
main() {
    #检查运行环境
    check_environment
    
    #设置权限
    set_permissions
    
    case "${1:-install}" in
        install)
            print_info "开始一键安装和启动 $APP_NAME 服务..."
            
            #快速安装
            quick_install
            
            #检查配置
            if ! check_configuration; then
                print_error "配置检查失败，请完善配置文件后重新运行"
                exit 1
            fi
            
            #启动服务
            start_service
            
            #显示访问信息
            show_access_info
            ;;
            
        setup)
            print_info "仅安装环境..."
            quick_install
            print_success "环境安装完成，请编辑配置文件后手动启动服务"
            ;;
            
        start)
            print_info "仅启动服务..."
            
            if ! check_configuration; then
                print_error "配置检查失败，请先完善配置文件"
                exit 1
            fi
            
            start_service
            show_access_info
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