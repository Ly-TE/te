#!/bin/bash
# 更新HTML文件到服务器的脚本

SERVER_IP="192.168.3.101"
REMOTE_PATH="/home/ubuntu/tool_box_front/templates/"

echo "开始更新HTML文件到服务器..."

# 检查本地文件是否存在
if [ ! -f "E:\\te\\tool_box_front\\templates\\user_register.html" ]; then
    echo "错误: 本地user_register.html文件不存在"
    exit 1
fi

if [ ! -f "E:\\te\\tool_box_front\\templates\\user_duration.html" ]; then
    echo "错误: 本地user_duration.html文件不存在"
    exit 1
fi

echo "正在上传user_register.html..."
scp "E:\\te\\tool_box_front\\templates\\user_register.html" ubuntu@$SERVER_IP:$REMOTE_PATH
if [ $? -eq 0 ]; then
    echo "✓ user_register.html 上传成功"
else
    echo "✗ user_register.html 上传失败"
    exit 1
fi

echo "正在上传user_duration.html..."
scp "E:\\te\\tool_box_front\\templates\\user_duration.html" ubuntu@$SERVER_IP:$REMOTE_PATH
if [ $? -eq 0 ]; then
    echo "✓ user_duration.html 上传成功"
else
    echo "✗ user_duration.html 上传失败"
    exit 1
fi

echo "正在重启服务器上的应用..."
ssh ubuntu@$SERVER_IP << 'EOF'
cd /home/ubuntu/tool_box_front
source venv/bin/activate
pkill -f "python.*app.py" || true
sleep 2
nohup python app.py > app.log 2>&1 &
echo "应用已重启"
EOF

if [ $? -eq 0 ]; then
    echo "✓ 应用已成功重启"
else
    echo "✗ 应用重启可能存在问题"
fi

echo "所有HTML文件已更新到服务器!"
echo "请访问 http://192.168.3.101:5000 检查更新是否生效"