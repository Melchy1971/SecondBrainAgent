$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot
# Kompatibilitaet: startet seit v30.25 die native Desktop-App.
python launcher.py native-gui @args
