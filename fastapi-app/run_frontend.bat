@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================
echo   数据科学家 Agent - Vue 前端
echo ==========================================
echo.
echo 正在启动，请稍候...
echo 启动后访问: http://localhost:5173
echo.

cd frontend
call npm run dev

echo.
echo 前端已关闭。
pause
