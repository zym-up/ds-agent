@echo off
set "PROJ=%~dp0.."
"%PROJ%\venv\Scripts\python.exe" -m uvicorn fastapi-app.backend.main:app --host 0.0.0.0 --port 8502 --reload
pause
