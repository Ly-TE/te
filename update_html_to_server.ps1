# PowerShell脚本：更新HTML文件到服务器

$SERVER_IP = "192.168.3.101"
$REMOTE_PATH = "/home/ubuntu/tool_box_front/templates/"
$LOCAL_PATH = "E:\te\tool_box_front\templates\"

Write-Host "开始更新HTML文件到服务器..."

# 检查本地文件是否存在
if (!(Test-Path "$LOCAL_PATH\user_register.html")) {
    Write-Host "错误: 本地user_register.html文件不存在" -ForegroundColor Red
    exit 1
}

if (!(Test-Path "$LOCAL_PATH\user_duration.html")) {
    Write-Host "错误: 本地user_duration.html文件不存在" -ForegroundColor Red
    exit 1
}

Write-Host "正在上传user_register.html..."
$uploadResult1 = & scp "$LOCAL_PATH\user_register.html" "ubuntu@$SERVER_IP`:$REMOTE_PATH" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ user_register.html 上传成功" -ForegroundColor Green
} else {
    Write-Host "✗ user_register.html 上传失败: $uploadResult1" -ForegroundColor Red
    exit 1
}

Write-Host "正在上传user_duration.html..."
$uploadResult2 = & scp "$LOCAL_PATH\user_duration.html" "ubuntu@$SERVER_IP`:$REMOTE_PATH" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ user_duration.html 上传成功" -ForegroundColor Green
} else {
    Write-Host "✗ user_duration.html 上传失败: $uploadResult2" -ForegroundColor Red
    exit 1
}

Write-Host "正在重启服务器上的应用..."
$restartScript = @"
cd /home/ubuntu/tool_box_front
source venv/bin/activate
pkill -f "python.*app.py" || true
sleep 2
nohup python app.py > app.log 2>&1 &
echo "应用已重启"
"@

$restartResult = & ssh ubuntu@$SERVER_IP $restartScript 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 应用已成功重启" -ForegroundColor Green
} else {
    Write-Host "✗ 应用重启可能存在问题: $restartResult" -ForegroundColor Yellow
}

Write-Host "所有HTML文件已更新到服务器!" -ForegroundColor Cyan
Write-Host "请访问 http://$SERVER_IP`:5000 检查更新是否生效" -ForegroundColor Cyan