$ErrorActionPreference = "Stop"
$Desktop = [Environment]::GetFolderPath("Desktop")
$Startup = [Environment]::GetFolderPath("Startup")
$Links = @(
  (Join-Path $Desktop "Jarvis GUI.lnk"),
  (Join-Path $Desktop "Jarvis HUD.lnk"),
  (Join-Path $Startup "Jarvis GUI Autostart.lnk"),
  (Join-Path $Startup "Jarvis HUD.lnk")
)
foreach ($Link in $Links) {
  if (Test-Path $Link) { Remove-Item $Link -Force; Write-Host "Entfernt: $Link" }
}
Write-Host "Jarvis Desktop-/Autostart-Verknuepfungen entfernt."
