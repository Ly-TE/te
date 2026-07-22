@echo off
REM 启动 Tool Box Front 服务 (Windows)

cd /d "%~dp0"
call venv\Scripts\activate.bat

echo 启动 Tool Box Front 服务...
python run.py

pause