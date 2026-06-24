@echo off
REM ============================================================
REM  Jarvis Voice Control v20
REM  Aufruf:
REM    Jarvis-Voice            -> Dauerbetrieb mit Wake-Word "Jarvis"
REM    Jarvis-Voice diagnose   -> Provider-/HUD-Status pruefen
REM    Jarvis-Voice once       -> eine Aeusserung aufnehmen
REM  Voraussetzung: laufendes HUD (Jarvis.bat) fuer RAG/Status/Skripte.
REM ============================================================
setlocal
set "ROOT=%~dp0"
set "PY=python"
where python >nul 2>nul || set "PY=py"

if /i "%~1"=="diagnose" (
  %PY% "%ROOT%scripts\jarvis_voice.py" --diagnose
  goto :end
)
if /i "%~1"=="once" (
  %PY% "%ROOT%scripts\jarvis_voice.py" --once
  goto :end
)
%PY% "%ROOT%scripts\jarvis_voice.py" --loop

:end
endlocal
