@echo off
setlocal
cd /d "%~dp0"
REM v30.25: Native Desktop ist der Primaerstart. Web-HUD nur noch mit: Jarvis.bat hud
python launcher.py jarvis %*
if errorlevel 1 pause
