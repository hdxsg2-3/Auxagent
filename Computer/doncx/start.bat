@echo off
chcp 65001 >nul
title 跨境电商AI助手 - 启动中...

echo ============================================
echo   跨境电商AI助手 - 一键启动
echo ============================================
echo.

:: 获取当前脚本所在目录
set "ROOT_DIR=%~dp0"
set "BACKEND_DIR=%ROOT_DIR%backend"
set "FRONTEND_DIR=%ROOT_DIR%frontend"

:: 检查 Python 是否可用
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

:: 检查 Node.js 是否可用
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Node.js，请先安装 Node.js 18+
    pause
    exit /b 1
)

:: 检查 .env 文件
if not exist "%ROOT_DIR%.env" (
    echo [警告] 未找到 .env 配置文件！
    echo 请将 .env.example 复制为 .env 并填入你的 API Key
    echo.
)

:: 启动后端服务
echo [1/2] 启动后端服务 (端口 5000)...
start "后端服务" cmd /c "cd /d "%BACKEND_DIR%" && python app.py"

:: 等待后端启动
timeout /t 2 /nobreak >nul

:: 启动前端服务
echo [2/2] 启动前端服务 (端口 5173)...
start "前端服务" cmd /c "cd /d "%FRONTEND_DIR%" && npm run dev"

:: 等待前端启动
timeout /t 3 /nobreak >nul

echo.
echo ============================================
echo   启动完成！
echo.
echo   后端地址: http://localhost:5000
echo   前端地址: http://localhost:5173
echo ============================================
echo.
echo 正在打开浏览器...
start http://localhost:5173

echo.
echo 提示：关闭此窗口不会停止服务，请关闭对应的 cmd 窗口。
echo.
pause