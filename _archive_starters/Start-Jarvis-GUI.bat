@echo off
setlocal
cd /d "%~dp0.."
REM Kompatibilitaetsdatei: startet den aktuellen nativen Jarvis-Desktop.
set "PY=python"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
"%PY%" launcher.py jarvis %*
if errorlevel 1 pause
endlocal
