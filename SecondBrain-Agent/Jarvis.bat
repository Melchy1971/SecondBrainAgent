@echo off
REM ============================================================
REM  Jarvis  -  startet das SecondBrain HUD (Port 8851)
REM  Aufruf:  Jarvis           (startet + oeffnet Browser)
REM           Jarvis /quiet    (startet ohne Browser, fuer Autostart)
REM ============================================================
setlocal EnableDelayedExpansion
set "ROOT=%~dp0"
set "PIDFILE=%ROOT%runtime\jarvis_hud.pid"
set "URL=http://127.0.0.1:8851"

set "QUIET="
if /i "%~1"=="/quiet" set "QUIET=1"
if /i "%~1"=="-quiet" set "QUIET=1"

REM --- laeuft bereits? ---
if exist "%PIDFILE%" (
  set /p PID=<"%PIDFILE%"
  tasklist /FI "PID eq !PID!" 2>nul | find "!PID!" >nul
  if not errorlevel 1 (
    if not defined QUIET (
      echo Jarvis laeuft bereits ^(PID !PID!^). Oeffne %URL%
      start "" "%URL%"
    )
    goto :end
  )
)

REM --- pythonw bevorzugen (kein Konsolenfenster), sonst python ---
set "PY=pythonw"
where pythonw >nul 2>nul || set "PY=python"

if not defined QUIET echo Starte Jarvis HUD ...
pushd "%ROOT%"
start "Jarvis HUD" %PY% "scripts\start_hud.py"
popd

REM --- Browser nur im normalen Modus ---
if not defined QUIET (
  timeout /t 2 /nobreak >nul
  start "" "%URL%"
  echo Jarvis HUD laeuft: %URL%   (stoppen mit: Jarvis-stop)
)

:end
endlocal
