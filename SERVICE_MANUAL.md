# Flask Web服务管理脚本使用说明

##概

这是一套完整的Linux系统下Flask Web应用服务管理脚本，包含启动、停止、重启、状态查看、日志管理等功能。

##脚列表

###核心管理脚本
- `start_service.sh` -启动服务
- `stop_service.sh` -停止服务  
- `restart_service.sh` - 重启服务
- `status_service.sh` - 查看服务状态
- `logs_service.sh` - 日志管理
- `manage_service.sh` - 交互式管理界面

### 安装脚本
- `install_service.sh` -安装和初始化

## 使用方法

### 1.环境安装
```bash
#首次使用前运行安装脚本
./install_service.sh

# 或者分步执行
./install_service.sh check      #检查依赖
./install_service.sh venv        # 创建虚拟环境
./install_service.sh deps        # 安装依赖
./install_service.sh config      #配置环境
```

### 2. 服务管理
```bash
#启动服务
./start_service.sh start

#停止服务
./stop_service.sh stop

# 重启服务
./restart_service.sh restart

# 查看状态
./status_service.sh status
```

### 3. 交互式管理
```bash
#启动交互式管理界面
./manage_service.sh

# 或者直接执行命令
./manage_service.sh start    #启动服务
./manage_service.sh status   # 查看状态
```

### 4. 日志管理
```bash
# 查看访问日志
./logs_service.sh access 100

# 查看错误日志
./logs_service.sh error 50

# 实时监控日志
./logs_service.sh follow access

# 搜索日志内容
./logs_service.sh search "error"

# 查看日志统计
./logs_service.sh stats
```

##配置说明

###环境变量文件 (.env)
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
如果选择创建systemd服务，可以使用系统命令管理:
```bash
sudo systemctl start tool_box_front.service
sudo systemctl stop tool_box_front.service
sudo systemctl status tool_box_front.service
sudo systemctl restart tool_box_front.service
```

##目录结构
```
tool_box_front/
├── app.py                 # Flask应用主文件
├── start_service.sh       #启动脚本
├── stop_service.sh        #停止脚本
├── restart_service.sh     # 重启脚本
├── status_service.sh      #状态查看脚本
├── logs_service.sh        # 日志管理脚本
├── manage_service.sh      # 交互式管理脚本
├── install_service.sh     # 安装脚本
├── venv/                  # Python虚拟环境
├── logs/                  # 日志文件目录
├── .env                  # 环境配置文件
└── requirements.txt       # Python依赖列表
```

## 注意事项

1. **权限设置**:首次使用前需要给脚本执行权限
   ```bash
   chmod +x *.sh
   ```

2. **依赖检查**:系统已安装Python3、pip3等基础依赖

3. **配置文件**: 使用前请编辑`.env`文件配置正确的数据库连接参数

4. **端口占用**: 默认使用5000端口，请确保端口未被占用

5. **日志管理**: 日志文件会自动轮转，建议定期清理

##故障排除

###常见问题
1. **服务启动失败**:检查端口占用和配置文件
2. **权限错误**:确保脚本有执行权限
3. **依赖缺失**:运行安装脚本重新安装依赖
4. **数据库连接失败**: 检查`.env`配置文件中的数据库参数

### 日志查看
```bash
# 查看错误日志
./logs_service.sh error

# 实时监控
./logs_service.sh follow error
```

##安全建议

1. 不要在生产环境中使用默认的SECRET_KEY
2.配置文件权限设置为600
3.定更新Python依赖包
4. 使用非root用户运行服务