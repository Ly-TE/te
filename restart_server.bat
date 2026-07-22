@echo off
REM 重启 Tool Box Front 服务 (Windows)

echo 重启 Tool Box Front 服务...
taskkill /f /im python.exe 2>nul
timeout /t 3 /nobreak >nul
call start_server.bat