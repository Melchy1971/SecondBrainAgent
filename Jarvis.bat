@echo off
setlocal
cd /d "%~dp0"
py -3 launcher.py jarvis
if errorlevel 1 (
  python launcher.py jarvis
)
endlocal
