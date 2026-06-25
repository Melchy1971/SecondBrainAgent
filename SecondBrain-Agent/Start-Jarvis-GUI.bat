@echo off
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%"
python launcher.py gui-open --project-root "%ROOT%"
endlocal
