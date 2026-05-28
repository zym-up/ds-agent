@echo off
chcp 65001 >nul

echo ==========================================
echo   DS Agent - Vue Frontend
echo ==========================================
echo.
echo Starting Vite dev server...
echo Open: http://localhost:5173
echo Press Ctrl+C to stop
echo ==========================================
echo.

cd /d "%~dp0"
if not exist "frontend\package.json" (
    echo [ERROR] frontend\package.json not found
    pause
    exit /b 1
)
cd frontend
npm run dev
pause
