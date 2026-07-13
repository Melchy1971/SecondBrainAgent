$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot
$env:HUD_RELOAD = "1"
Write-Host "================================================================"
Write-Host " Jarvis HUD - DEV-Modus (Auto-Reload)"
Write-Host " Server startet bei jeder Code-Aenderung automatisch neu."
Write-Host " Browser:  http://127.0.0.1:8851"
Write-Host " Stoppen:  Strg+C"
Write-Host "================================================================"
python scripts\start_hud.py
