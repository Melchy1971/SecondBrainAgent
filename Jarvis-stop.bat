@echo off
REM ============================================================
REM  Jarvis-stop  -  stoppt das SecondBrain HUD (Port 8851)
REM  Aufruf:  Jarvis-stop
REM ============================================================
setlocal EnableDelayedExpansion
set "ROOT=%~dp0"
set "PIDFILE=%ROOT%runtime\jarvis_hud.pid"
set "KILLED="

REM --- per PID-Datei beenden ---
if exist "%PIDFILE%" (
  set /p PID=<"%PIDFILE%"
  taskkill /PID !PID! /F >nul 2>nul && set "KILLED=1"
  del "%PIDFILE%" >nul 2>nul
)

REM --- Fallback: alles was auf Port 8851 lauscht beenden ---
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8851" ^| findstr LISTENING') do (
  taskkill /PID %%a /F >nul 2>nul && set "KILLED=1"
)

if defined KILLED (
  echo Jarvis HUD gestoppt.
) else (
  echo Jarvis HUD lief nicht.
)
endlocal
