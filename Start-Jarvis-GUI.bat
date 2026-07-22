@echo off
setlocal
cd /d "%~dp0"
REM Nativer Jarvis-Desktop mit eingebetteter Web-GUI (QWebEngine). Alias zu Jarvis.bat.
REM Fuer das Web-HUD im Browser stattdessen HUD.bat verwenden.
set "PY=python"
if exist "%~dp0.venv\Scripts\python.exe" set "PY=%~dp0.venv\Scripts\python.exe"
"%PY%" launcher.py native-web-shell %*
if errorlevel 1 pause
