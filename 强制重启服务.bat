@echo off
chcp 65001 >nul
echo ================================================
echo 🔄 正在完全重启 Flask 服务...
echo ================================================

REM 强制杀死所有 Python 进程
taskkill /F /IM python.exe >nul 2>&1
timeout /t 5 /nobreak >nul

REM 清理 Python 缓存
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "*.pyc" del /q "*.pyc"

echo ✅ Python 进程已清理
echo ✅ 缓存已清理

echo.
echo 🚀 正在启动 Flask 服务...
echo ================================================

cd /d "%~dp0"
start "Flask 服务 - 请勿关闭此窗口" python app.py

echo.
echo ✅ Flask 服务已启动!
echo 📍 访问地址：http://10.1.3.31:5000/qr_code.html
echo.
echo 📋 请按任意键查看启动日志..."
pause >nul
