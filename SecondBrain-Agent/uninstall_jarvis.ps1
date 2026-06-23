# ============================================================
#  uninstall_jarvis.ps1
#  Entfernt Desktop- und Autostart-Verknuepfung des Jarvis HUD.
#  Aufruf:
#   powershell -ExecutionPolicy Bypass -File uninstall_jarvis.ps1
# ============================================================
$desktop = [Environment]::GetFolderPath("Desktop")
$startup = [Environment]::GetFolderPath("Startup")

$targets = @(
  (Join-Path $desktop "Jarvis HUD.lnk"),
  (Join-Path $startup "Jarvis HUD.lnk")
)

foreach ($t in $targets) {
  if (Test-Path $t) {
    Remove-Item $t -Force
    Write-Host "Entfernt: $t"
  } else {
    Write-Host "Nicht vorhanden: $t"
  }
}
Write-Host "Fertig."
