@echo off
setlocal
cd /d "%~dp0.."
set "PY=python"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
echo SecondBrain-Agent Installation Windows
"%PY%" -m pip install --upgrade pip
if errorlevel 1 goto :error
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 goto :error
echo.
echo Optionale Pakete installieren?
echo "%PY%" -m pip install -r requirements-optional.txt
pause
endlocal
exit /b 0
:error
echo FEHLER bei der Installation.
pause
endlocal
exit /b 1
