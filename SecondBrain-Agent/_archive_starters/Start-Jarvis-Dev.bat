@echo off
setlocal
cd /d "%~dp0"
set HUD_RELOAD=1
echo ================================================================
echo  Jarvis HUD - DEV-Modus (Auto-Reload)
echo  Server startet bei jeder Code-Aenderung automatisch neu.
echo  Browser:  http://127.0.0.1:8851
echo  Stoppen:  Strg+C
echo ================================================================
python scripts\start_hud.py
if errorlevel 1 pause
