@echo off
setlocal
cd /d "%~dp0"
python launcher.py hud %*
if errorlevel 1 pause
