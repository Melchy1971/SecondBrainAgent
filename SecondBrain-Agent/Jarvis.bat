@echo off
REM ============================================================
REM Jarvis GUI - stabiler Startpfad fuer Desktop-Verknuepfung
REM
REM Normal:   Jarvis.bat          -> startet GUI und Browser
REM Autostart Jarvis.bat /quiet   -> startet GUI ohne Browser
REM Diagnose: python launcher.py gui-doctor
REM ============================================================
setlocal EnableDelayedExpansion
set "ROOT=%~dp0"
cd /d "%ROOT%"

set "QUIET="
set "NOBROWSER="
if /i "%~1"=="/quiet" set "QUIET=--quiet --no-browser"
if /i "%~1"=="-quiet" set "QUIET=--quiet --no-browser"
if /i "%~1"=="/no-browser" set "NOBROWSER=--no-browser"

where python >nul 2>nul
if errorlevel 1 (
  echo Python wurde nicht gefunden. Bitte Python installieren oder PATH pruefen.
  pause
  exit /b 1
)

python launcher.py gui-open --project-root "%ROOT%" %QUIET% %NOBROWSER%
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo.
  echo GUI-Start fehlgeschlagen. Diagnose:
  python launcher.py gui-doctor --project-root "%ROOT%"
  pause
)
exit /b %RC%
