@echo off
setlocal
cd /d "%~dp0"
REM Startet das MediaMTX-Gateway mit config\mediamtx.yml (RTSP -> WebRTC/HLS).
set "MTX="
if exist "%~dp0mediamtx.exe" set "MTX=%~dp0mediamtx.exe"
if exist "%~dp0tools\mediamtx\mediamtx.exe" set "MTX=%~dp0tools\mediamtx\mediamtx.exe"
if not defined MTX (
  echo mediamtx.exe nicht gefunden.
  echo Lade es von:  https://github.com/bluenviron/mediamtx/releases/latest
  echo Entpacke mediamtx.exe nach:  %~dp0   ODER   %~dp0tools\mediamtx\
  echo Danach diese Datei erneut starten.
  pause
  exit /b 1
)
echo Starte MediaMTX-Gateway ... (Fenster offen lassen; Stop mit Strg+C)
"%MTX%" "%~dp0config\mediamtx.yml"
pause
