@echo off
setlocal
cd /d "%~dp0"
python launcher.py native-gui %*
if errorlevel 1 pause
