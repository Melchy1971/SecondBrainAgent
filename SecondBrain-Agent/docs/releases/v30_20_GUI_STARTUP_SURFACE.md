# v30.20 GUI Startup Surface

## Ziel

Alle GUI-Startpfade konsolidieren. Desktop-Verknüpfung, PowerShell, Batch, Launcher und alte Alias-Kommandos starten dieselbe Jarvis-GUI.

## Neue/aktualisierte Befehle

- `gui`
- `gui-start`
- `gui-open`
- `gui-status`
- `gui-doctor`
- `gui-shortcuts`
- `desktop-gui`
- `desktop16-gui`

## Wirkung

- Kein Bruch mehr durch veraltetes `desktop16-gui`.
- `Jarvis.bat` nutzt den Launcher statt direkt interner Skripte.
- Desktop-/Autostart-Verknüpfungen werden über `Install-Jarvis-Desktop.ps1` erstellt.
- `install_jarvis.ps1` bleibt als kompatibler Wrapper erhalten.
