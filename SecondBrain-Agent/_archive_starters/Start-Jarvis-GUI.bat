@echo off
setlocal
cd /d "%~dp0"
REM Kompatibilitaetsdatei: startet seit v30.25 die native Desktop-App.
python launcher.py native-gui %*
if errorlevel 1 pause
