$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Bat = Join-Path $Root "Jarvis.bat"
if (-not (Test-Path $Bat)) { throw "Jarvis.bat nicht gefunden: $Bat" }

$Shell = New-Object -ComObject WScript.Shell
$Desktop = [Environment]::GetFolderPath("Desktop")
$Startup = [Environment]::GetFolderPath("Startup")
$Icon = Join-Path $Root "jarvis.ico"
if (-not (Test-Path $Icon)) { $Icon = "$env:SystemRoot\System32\shell32.dll,13" }

$DesktopLink = Join-Path $Desktop "Jarvis GUI.lnk"
$d = $Shell.CreateShortcut($DesktopLink)
$d.TargetPath = $Bat
$d.WorkingDirectory = $Root
$d.WindowStyle = 7
$d.Description = "SecondBrain Jarvis GUI starten"
$d.IconLocation = $Icon
$d.Save()

$StartupLink = Join-Path $Startup "Jarvis GUI Autostart.lnk"
$a = $Shell.CreateShortcut($StartupLink)
$a.TargetPath = $Bat
$a.Arguments = "/quiet"
$a.WorkingDirectory = $Root
$a.WindowStyle = 7
$a.Description = "SecondBrain Jarvis GUI beim Windows-Start laden"
$a.IconLocation = $Icon
$a.Save()

Write-Host "Desktop-Verknuepfung erstellt: $DesktopLink"
Write-Host "Autostart-Verknuepfung erstellt: $StartupLink"
Write-Host "Start: Doppelklick auf 'Jarvis GUI' oder: python launcher.py gui-open"
