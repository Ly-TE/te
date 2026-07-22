# Flask Web服务管理套件

一套完整的Linux系统下Flask Web应用服务管理脚本，包含安装、启动、停止、重启、状态查看、日志管理等全套功能。

##快速开始

### 一键安装启动
```bash
#给本添加执行权限
chmod +x *.sh

# 一键安装并启动服务
./quick_start.sh install
```

### 分步操作
```bash
# 1.环境安装
./install_service.sh

# 2.编辑配置文件
vim .env

# 3.启动服务
./start_service.sh start

# 4. 查看状态
./status_service.sh status
```

## 🚀 部署到远程服务器

### 使用部署脚本
```bash
# 给部署脚本添加执行权限
chmod +x deploy_to_server.sh

# 完整部署到远程服务器
./deploy_to_server.sh deploy username@192.168.3.101

# 或者分步操作：
# 1. 仅上传代码
./deploy_to_server.sh upload username@192.168.3.101

# 2. 仅在服务器上设置环境
./deploy_to_server.sh setup username@192.168.3.101
```

### 手动部署
参考 `DEPLOY_TO_SERVER.md` 文件获取详细的部署指南。

## 🔧 常见问题解决

### OpenSSL兼容性问题
如果在CentOS/RHEL等系统上遇到以下错误：
```
urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'OpenSSL 1.0.2k-fips'
```

可以使用修复脚本：
```bash
# 给修复脚本添加执行权限
chmod +x fix_openssl_issue.sh

# 修复OpenSSL兼容性问题
./fix_openssl_issue.sh fix-openssl root@192.168.3.101

# 或者执行完整修复流程
./fix_openssl_issue.sh full-fix root@192.168.3.101
```

此问题已在最新的requirements.txt中解决，新部署将自动包含兼容性修复。

### 服务无法访问问题
如果无法访问 http://192.168.3.101:5000，请使用诊断脚本：

```bash
# 给诊断脚本添加执行权限
chmod +x diagnose_connection.sh

# 诊断连接问题
./diagnose_connection.sh diagnose root@192.168.3.101

# 或者修复所有常见问题
./diagnose_connection.sh fix-all root@192.168.3.101

# 检查服务状态
./diagnose_connection.sh check-service root@192.168.3.101
```

更多信息请参见 `TROUBLESHOOTING_GUIDE.md` 文件。

## 📋 功能特性

✅ **完整的服务管理**:启动、停止、重启、状态查看
- ✅ **智能依赖检查**: 自动检查和安装系统依赖
- ✅ **虚拟环境管理**: 自动创建和管理Python虚拟环境
- ✅ **日志管理系统**: 查看、搜索、实时监控日志
- ✅ **交互式管理界面**:友菜单式操作界面
- ✅ **配置文件管理**: 自动生成和管理环境配置
- ✅ **系统服务集成**:可选创建systemd服务文件
- ✅ **错误处理机制**:完善的错误检测和处理
- ✅ **安全权限控制**:合的理的文件权限设置
- ✅ **生产环境优化**: 支持Gunicorn、Nginx等生产环境配置
- ✅ **兼容性修复**:自动处理常见的系统兼容性问题

## 📁 脚说明

### 核心管理脚本
|名称 |功能说明 |
|---------|---------|
| `start_service.sh` | 启动 Flask 服务 |
| `stop_service.sh` | 停止 Flask 服务 |
| `restart_service.sh` | 重启Flask服务 |
| `status_service.sh` | 查看服务状态 |
| `logs_service.sh` | 日志管理 |
| `manage_service.sh` | 交互式管理界面 |

###安装配置脚本
|脚名称 |功能说明 |
|---------|---------|
| `install_service.sh` |完整环境安装 |
| `quick_start.sh` | 一键快速启动 |

###部署相关脚本
|脚本名称 |功能说明 |
|---------|---------|
| `deploy_to_server.sh` | 部署到远程服务器 |
| `fix_openssl_issue.sh` | 解决OpenSSL兼容性问题 |
| `diagnose_connection.sh` | 诊断连接问题 |
| `quick_fix_access.sh` | 快速修复访问问题 |

### 故障排除文档
| 文档名称 | 说明 |
|---------|------|
| `TROUBLESHOOTING_GUIDE.md` | 详细故障排除指南 |
| `ACCESS_ISSUE_SOLUTION.md` | 解决访问问题方案 |
| `API_UPDATE_NOTICE.md` | API接口更新说明 |


| `UPDATE_INSTRUCTIONS.md` | 服务器更新指南 |
| `DEPLOYMENT_GUIDE.md` | 完整部署运维指南 |

###配置文件
| 文件名称 | 说明 |
|---------|------|
| `.env` |环境配置文件 |
| `.env.example` |配置文件示例 |
| `requirements.txt` | Python依赖列表(包含可选依赖的注释说明) |

##🛠 使用示例

### 服务管理
```bash
# 启动服务
./start_service.sh start

# 停止服务
./stop_service.sh stop

# 注意：停止服务请使用 stop_service.sh，不要执行 ./start_service.sh stop

# 重启服务
./restart_service.sh restart

# 查看状态
./status_service.sh status
```

### 日志管理
```bash
# 查看访问日志
./logs_service.sh access 100

# 查看错误日志
./logs_service.sh error 50

# 实时监控
./logs_service.sh follow access

# 搜索日志
./logs_service.sh search "error"
```

### 交互式管理
```bash
#启动管理界面
./manage_service.sh

#直执行命令
./manage_service.sh start
./manage_service.sh status
```

##⚙配置说明

### 环境变量文件 (.env)
```bash
# Flask应用配置
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=your-secret-key-here

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_db_name

#应用配置
DEBUG=False
PORT=5000
HOST=0.0.0.0
```

### 系统服务配置 (可选)
```bash
# 创建systemd服务
./install_service.sh systemd

# 使用系统命令管理
sudo systemctl start tool_box_front.service
sudo systemctl status tool_box_front.service
```

## 📊 目录结构
```
tool_box_front/
├── app.py                 # Flask应用主文件
├── start_service.sh       # 启动脚本
├── stop_service.sh        # 停止脚本
├── restart_service.sh     # 重启脚本
├── status_service.sh      #状态查看脚本
├── logs_service.sh        # 日志管理脚本
├── manage_service.sh      # 交互式管理脚本
├── install_service.sh     #安装脚本
├── quick_start.sh         #快速启动脚本
├── venv/                  # Python虚拟环境
├── logs/                  # 日志文件目录
├── .env                  # 环境配置文件
└── requirements.txt       # Python依赖列表
```

##🔧系统要求

- **操作系统**: Linux (Ubuntu/CentOS/Debian等)
- **Python版本**: 3.6+
- **基础依赖**: python3, pip3, git
- **推荐内存**: 512MB+
- **推荐存储**: 100MB+

## 📝 注意事项

1. **首次使用**: 请确保系统已安装基础依赖
2. **权限设置**:首次运行需要给脚本执行权限
3. **配置文件**: 使用前请编辑`.env`文件配置数据库参数
4. **端口占用**: 默认使用5000端口，请确保端口可用
5. **安全建议**: 生产环境请修改默认SECRET_KEY

##🆘故障排除

###常见问题
1. **服务启动失败**:检查端口占用和配置文件
2. **权限错误**:确保脚本有执行权限
3. **依赖缺失**:运行安装脚本重新安装依赖
4. **数据库连接失败**: 检查`.env`配置文件

### 日志查看
```bash
# 查看详细错误信息
./logs_service.sh error

# 实时监控服务状态
./logs_service.sh follow all
```

##📖详细文档

查看 [SERVICE_MANUAL.md](SERVICE_MANUAL.md) 获取完整的使用说明和配置指南。

##🤝

欢迎提交Issue和Pull Request来改进这套服务管理脚本。

## 📄 许可证

MIT License