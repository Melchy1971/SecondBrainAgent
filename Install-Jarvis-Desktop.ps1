$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Target = Join-Path $Root "Jarvis.bat"
$Desktop = [Environment]::GetFolderPath("Desktop")
$StartMenu = Join-Path ([Environment]::GetFolderPath("StartMenu")) "Programs"
$Shell = New-Object -ComObject WScript.Shell
foreach ($Item in @(@{Path=(Join-Path $Desktop "Jarvis.lnk")}, @{Path=(Join-Path $StartMenu "Jarvis.lnk")})) {
  $Shortcut = $Shell.CreateShortcut($Item.Path)
  $Shortcut.TargetPath = $Target
  $Shortcut.WorkingDirectory = $Root
  $Shortcut.Description = "SecondBrain Agent Jarvis GUI"
  $Shortcut.Save()
}
Write-Host "Jarvis-Verknuepfungen erstellt."
