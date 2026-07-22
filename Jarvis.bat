@echo off
setlocal
cd /d "%~dp0"
REM Nativer Jarvis-Desktop: eigenes Fenster, Inhalt = die Web-GUI (QWebEngine).
REM Sieht exakt wie das Web-HUD aus. Faellt QtWebEngine aus, meldet es das und
REM man nutzt "launcher.py jarvis" (klassische Shell) oder HUD.bat (Browser).
set "PY=python"
if exist "%~dp0.venv\Scripts\python.exe" set "PY=%~dp0.venv\Scripts\python.exe"
"%PY%" launcher.py native-web-shell %*
if errorlevel 1 pause
