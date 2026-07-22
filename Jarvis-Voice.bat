@echo off
setlocal
cd /d "%~dp0"
REM Deutsche Sprachsteuerung: nimmt einen getippten Befehl entgegen und parst ihn.
set "PY=python"
if exist "%~dp0.venv\Scripts\python.exe" set "PY=%~dp0.venv\Scripts\python.exe"
set /p JARVIS_CMD=Deutscher Jarvis-Befehl:
"%PY%" launcher.py voice-command --text "%JARVIS_CMD%"
if errorlevel 1 pause
endlocal
