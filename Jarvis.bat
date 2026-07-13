@echo off
setlocal
cd /d "%~dp0"
REM Startet die richtige GUI: Web-Control-Center (http://127.0.0.1:8851).
set "PY=python"
if exist "%~dp0.venv\Scripts\python.exe" set "PY=%~dp0.venv\Scripts\python.exe"
"%PY%" launcher.py hud %*
if errorlevel 1 pause
