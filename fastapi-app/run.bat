@echo off
chcp 65001 >nul
title DS Agent - Backend

echo ==========================================
echo   DS Agent - FastAPI 后端
echo ==========================================
echo.

cd /d "%~dp0"

REM 获取项目根目录（fastapi-app 的上一级）
set "PROJ_DIR=%~dp0.."

REM 虚拟环境 Python 路径
set "PYTHON_PATH=%PROJ_DIR%\venv\Scripts\python.exe"

echo [1/3] 检查虚拟环境...
if not exist "%PYTHON_PATH%" (
    echo [错误] 找不到虚拟环境
    echo 路径: %PYTHON_PATH%
    echo.
    echo 请先运行 setup.bat 创建虚拟环境
    pause
    exit /b 1
)
echo [成功] 找到 Python: %PYTHON_PATH%
echo.

echo [2/3] 检查后端文件...
if not exist "backend\main.py" (
    echo [错误] 找不到 backend\main.py
    pause
    exit /b 1
)
echo [成功] 找到 backend\main.py
echo.

echo [3/3] 启动 FastAPI 服务器...
echo.
echo ==========================================
echo   访问地址: http://localhost:8502
echo   API 文档: http://localhost:8502/docs
echo   按 Ctrl+C 停止服务器
echo ==========================================
echo.

"%PYTHON_PATH%" -m uvicorn backend.main:app --host 127.0.0.1 --port 8502 --reload

pause
