@echo off
REM Tool Box Front Windows 部署脚本

setlocal enabledelayedexpansion

REM 配置变量
set PROJECT_NAME=tool_box_front
set PROJECT_DIR=%~dp0
set VENV_DIR=%PROJECT_DIR%venv

echo ========================================
echo Tool Box Front 部署脚本 (Windows)
echo ========================================

REM 检查是否以管理员权限运行
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 错误: 此脚本需要管理员权限运行
    echo 请右键点击"以管理员身份运行"
    pause
    exit /b 1
)

REM 检查Python是否安装
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo 错误: 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo [INFO] 创建Python虚拟环境...
cd /d "%PROJECT_DIR%"
python -m venv venv
if %errorLevel% neq 0 (
    echo 错误: 创建虚拟环境失败
    pause
    exit /b 1
)

echo [INFO] 激活虚拟环境并安装依赖...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip

REM 安装依赖
if exist "requirements-full.txt" (
    pip install -r requirements-full.txt
) else if exist "requirements.txt" (
    pip install -r requirements.txt
) else (
    echo 错误: 未找到requirements文件
    pause
    exit /b 1
)

echo [INFO] 配置环境变量...
if exist ".env.example" (
    copy ".env.example" ".env"
    echo 请编辑 .env 文件配置正确的环境变量
)

echo [INFO] 部署完成！
echo.
echo 使用说明:
echo 1. 编辑 .env 文件配置数据库连接和其他参数
echo 2. 运行 start_server.bat 启动服务
echo 3. 访问 http://localhost:5000
echo.
echo 服务管理:
echo - 启动服务: start_server.bat
echo - 停止服务: stop_server.bat
echo - 重启服务: restart_server.bat
echo.

pause