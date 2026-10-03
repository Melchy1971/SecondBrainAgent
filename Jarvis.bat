@echo off
setlocal
cd /d "%~dp0"
REM Startet den nativen, responsiven Jarvis-Desktop mit Sprachsteuerung.
REM Fuer das Web-HUD im Browser stattdessen HUD.bat verwenden.
set "PY=python"
if exist "%~dp0.venv\Scripts\python.exe" set "PY=%~dp0.venv\Scripts\python.exe"
"%PY%" launcher.py jarvis %*
if errorlevel 1 pause
endlocal
