@echo off
setlocal
cd /d "%~dp0"
echo ================================================================
echo  Jarvis Setup - virtuelle Umgebung + Abhaengigkeiten
echo ================================================================
if not exist ".venv\Scripts\python.exe" (
  echo [1/3] Erstelle .venv ...
  python -m venv .venv || ( echo FEHLER: venv-Erstellung fehlgeschlagen. Ist Python installiert? ^& pause ^& exit /b 1 )
) else (
  echo [1/3] .venv bereits vorhanden.
)
echo [2/3] Aktualisiere pip ...
".venv\Scripts\python.exe" -m pip install --upgrade pip
echo [3/3] Installiere deklarierte Abhaengigkeiten (dev,pdf,connectors,openai,desktop) ...
".venv\Scripts\python.exe" -m pip install -e ".[dev,pdf,connectors,openai,desktop]"
if errorlevel 1 ( echo. ^& echo FEHLER bei der Installation. ^& pause ^& exit /b 1 )
echo.
echo Fertig. Optional Sprachsteuerung:  .venv\Scripts\python.exe -m pip install -e ".[voice]"
echo Starten:  HUD.bat  (Web-HUD)   oder   Jarvis.bat  (nativer Desktop)
pause
