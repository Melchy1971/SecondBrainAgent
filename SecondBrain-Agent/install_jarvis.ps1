# ============================================================
#  install_jarvis.ps1
#  Legt zwei Verknuepfungen an:
#   1) Desktop  "Jarvis HUD"  -> startet HUD + oeffnet Browser
#   2) Autostart (Login)      -> startet HUD ohne Browser (/quiet)
#  Aufruf:
#   powershell -ExecutionPolicy Bypass -File install_jarvis.ps1
# ============================================================
$ErrorActionPreference = "Stop"

$Root = $PSScriptRoot
$Bat  = Join-Path $Root "Jarvis.bat"
if (-not (Test-Path $Bat)) { throw "Jarvis.bat nicht gefunden in $Root" }

$ws      = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath("Desktop")
$startup = [Environment]::GetFolderPath("Startup")

# --- 1) Desktop-Verknuepfung (mit Browser) ---
$d = $ws.CreateShortcut((Join-Path $desktop "Jarvis HUD.lnk"))
$d.TargetPath       = $Bat
$d.WorkingDirectory = $Root
$d.WindowStyle      = 7                 # minimiert starten
$d.Description      = "SecondBrain Jarvis HUD starten"
$d.IconLocation     = "shell32.dll,13"  # generisches Icon; bei Bedarf aendern
$d.Save()

# --- 2) Autostart-Verknuepfung (ohne Browser) ---
$a = $ws.CreateShortcut((Join-Path $startup "Jarvis HUD.lnk"))
$a.TargetPath       = $Bat
$a.Arguments        = "/quiet"
$a.WorkingDirectory = $Root
$a.WindowStyle      = 7
$a.Description      = "SecondBrain Jarvis HUD beim Login starten"
$a.IconLocation     = "shell32.dll,13"
$a.Save()

Write-Host "Desktop-Verknuepfung : $desktop\Jarvis HUD.lnk"
Write-Host "Autostart            : $startup\Jarvis HUD.lnk"
Write-Host "Fertig. Entfernen mit: uninstall_jarvis.ps1"
