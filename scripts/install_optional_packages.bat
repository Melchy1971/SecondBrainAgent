@echo off
setlocal
cd /d "%~dp0.."
set "PY=python"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
"%PY%" -m pip install --upgrade pip
if errorlevel 1 goto :error
"%PY%" -m pip install pypdf requests beautifulsoup4
if errorlevel 1 goto :error
echo Optionale Pakete wurden installiert.
pause
endlocal
exit /b 0
:error
echo FEHLER bei der Installation.
pause
endlocal
exit /b 1
