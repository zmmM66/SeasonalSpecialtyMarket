@echo off
echo 正在启动时令特色产品市场Web应用...
echo.
echo 正在启动Flask后端服务器...
start python app.py
echo Flask服务器已在后台启动 (端口: 5000)
echo.
echo 正在启动前端服务器...
cd frontend
start python -m http.server 8080
echo 前端服务器已启动 (端口: 8080)
echo.
echo ========================================
echo 应用已启动！请访问以下地址：
echo http://localhost:8080
echo ========================================
echo.
echo 按任意键关闭此窗口...
pause >nul