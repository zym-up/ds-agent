@echo off
set "PROJ=%~dp0.."
"%PROJ%\venv\Scripts\python.exe" -m streamlit run "%~dp0app.py" --server.port 8501 --server.headless true --browser.gatherUsageStats false
pause
