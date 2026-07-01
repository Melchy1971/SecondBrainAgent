@echo off
setlocal
cd /d "%~dp0"
set /p JARVIS_CMD=Deutscher Jarvis-Befehl: 
python launcher.py voice-parse %JARVIS_CMD%
endlocal
