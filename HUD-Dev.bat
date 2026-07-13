@echo off
setlocal
cd /d "%~dp0"
set HUD_RELOAD=1
set "PY=python"
if exist "%~dp0.venv\Scripts\python.exe" set "PY=%~dp0.venv\Scripts\python.exe"
echo Jarvis Web-HUD DEV (Auto-Reload) - http://127.0.0.1:8851 - Stop: Strg+C
"%PY%" scripts\start_hud.py
if errorlevel 1 pause
