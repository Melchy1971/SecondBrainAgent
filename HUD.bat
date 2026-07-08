@echo off
setlocal
cd /d "%~dp0"
REM Web-HUD auf http://127.0.0.1:8851 (funktionierende Menues, Security-Panel).
set "PY=python"
if exist "%~dp0.venv\Scripts\python.exe" set "PY=%~dp0.venv\Scripts\python.exe"
"%PY%" launcher.py hud %*
if errorlevel 1 pause
