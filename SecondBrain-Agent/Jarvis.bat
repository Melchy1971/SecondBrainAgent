@echo off
setlocal
cd /d "%~dp0"
python launcher.py jarvis %*
if errorlevel 1 pause
