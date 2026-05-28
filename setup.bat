@echo off
echo ==========================================
echo   DS Agent - Setup
echo ==========================================
echo.
python --version >/dev/null 2>&1
if errorlevel 1 (
echo [ERROR] Python not found. Install Python 3.11+ first.
echo Download: https://www.python.org/downloads/
echo Check: "Add Python to PATH" during install.
pause
exit /b 1
)
python --version
echo.
echo Creating virtual environment...
python -m venv venv
echo.
echo Installing dependencies...
venv\Scripts\pip install -r streamlit-app\requirements.txt -q
echo.
echo ==========================================
echo   Setup complete!
echo ==========================================
echo.
echo To start:
echo   Streamlit: double-click streamlit-app\run.bat
echo   FastAPI:   double-click fastapi-app\run_backend.bat
echo.
pause
