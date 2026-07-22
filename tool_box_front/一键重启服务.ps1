# ================================================
# 🚀 一键重启 Flask 服务并验证路由
# ================================================

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "🔄 正在完全重启 Flask 服务..." -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: 强制停止所有 Python 进程
Write-Host "⏹️  步骤 1: 停止所有 Python 进程..." -ForegroundColor Yellow
try {
    Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 3
    Write-Host "✅ Python 进程已清理" -ForegroundColor Green
} catch {
    Write-Host "⚠️  清理进程时出错，继续执行..." -ForegroundColor Yellow
}
Write-Host ""

# Step 2: 清理缓存
Write-Host "🧹 步骤 2: 清理 Python 缓存..." -ForegroundColor Yellow
$cacheDirs = @(
    (Join-Path $PSScriptRoot "__pycache__"),
    (Join-Path $PSScriptRoot "*.pyc")
)
foreach ($cache in $cacheDirs) {
    if (Test-Path $cache) {
        Remove-Item $cache -Recurse -Force -ErrorAction SilentlyContinue
    }
}
Write-Host "✅ 缓存已清理" -ForegroundColor Green
Write-Host ""

# Step 3: 启动 Flask 服务
Write-Host "🚀 步骤 3: 启动 Flask 服务..." -ForegroundColor Yellow
Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "📋 服务启动中，请稍候..." -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# 使用新窗口启动
Start-Process python -ArgumentList "app.py" -WorkingDirectory $PSScriptRoot -WindowStyle NewWindow

Write-Host "✅ Flask 服务已在新窗口启动!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 访问地址：" -NoNewline
Write-Host "http://10.1.3.31:5000/qr_code.html" -ForegroundColor Green
Write-Host ""
Write-Host "🔍 验证步骤:" -ForegroundColor Cyan
Write-Host "  1. 在新打开的 Flask 窗口中查找以下信息:" -ForegroundColor White
Write-Host "     ✅ /api/qr-decode 路由已注册!" -ForegroundColor Green
Write-Host ""
Write-Host "  2. 在浏览器中按 Ctrl+F5 强制刷新" -ForegroundColor White
Write-Host ""
Write-Host "  3. 在浏览器控制台测试接口:" -ForegroundColor White
Write-Host @"
     fetch('http://10.1.3.31:5000/api/qr-decode', {
       method: 'OPTIONS'
     }).then(r => console.log('状态:', r.status))
"@ -ForegroundColor Gray
Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "⏳ 等待 10 秒后自动检查服务状态..." -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

Start-Sleep -Seconds 10

# Step 4: 检查服务是否运行
Write-Host ""
Write-Host "🔍 检查服务状态..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://10.1.3.31:5000/" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Flask 服务运行正常!" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Flask 服务可能未正确启动" -ForegroundColor Red
    Write-Host "   错误：$($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "请检查新打开的 Flask 窗口中的日志信息" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
