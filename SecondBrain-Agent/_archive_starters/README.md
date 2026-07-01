# Archivierte Start-Dateien

Am 2026-07-01 im Zuge der Start-Datei-Bereinigung hierher verschoben (nicht geloescht).
Alle waren redundant, fehlerhaft oder Altlast. Nichts davon wird fuer den Betrieb gebraucht.

## Kanonischer Satz (im Projektroot verbleibend)
- `Jarvis.bat`        -> nativer Desktop  (`launcher.py jarvis`)
- `HUD.bat`           -> Web-HUD 127.0.0.1:8851  (`launcher.py hud`)
- `HUD-Dev.bat`       -> Web-HUD mit Auto-Reload  (`scripts/start_hud.py`, HUD_RELOAD=1)
- `Jarvis-Voice.bat`  -> Sprachsteuerung
- `Jarvis-stop.bat`   -> HUD auf Port 8851 beenden
- `Install-Jarvis-Desktop.ps1` / `uninstall_jarvis.ps1` -> Verknuepfungen
- `scripts/start_hud.py` -> eigentlicher Server-Bootstrap (Kern)

## Warum archiviert
- `Start-Jarvis-Native.bat/.ps1`, `Start-Jarvis-GUI.bat/.ps1` -> Duplikate von `Jarvis.bat` (nativer Start).
- `Start-Jarvis-WebHUD.bat` -> durch `HUD.bat` ersetzt (klarerer Name).
- `Start-Jarvis-Dev.bat/.ps1` -> durch `HUD-Dev.bat` ersetzt.
- `install_jarvis.ps1` -> Einzeiler-Wrapper um `Install-Jarvis-Desktop.ps1`.
- `scripts/start.py` -> No-op-Stub (`print(...)`).
- `scripts/start.bat` -> hartkodierter Pfad `H:\...`, fragil.
- `scripts/start_desktop.ps1`, `start_gui.py`, `start_jarvis.py`, `start_jarvis_gui.py` -> Duplikate (`gui-open`/`jarvis`).
- `scripts/start_desktop_gui.py` -> zweites, paralleles GUI-Stack (`secondbrain.desktop.gui`), Altlast.

Kann nach Pruefung geloescht werden.
