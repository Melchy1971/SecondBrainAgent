# Jarvis GUI starten

## Standardstart

```powershell
python launcher.py gui-open
```

Alias-Kommandos:

```powershell
python launcher.py gui
python launcher.py gui-start
python launcher.py desktop-gui
python launcher.py desktop16-gui
```

## Status und Diagnose

```powershell
python launcher.py gui-status
python launcher.py gui-doctor
python launcher.py gui-shortcuts
```

## Windows Desktop-Verknüpfung erstellen

```powershell
powershell -ExecutionPolicy Bypass -File Install-Jarvis-Desktop.ps1
```

Erzeugt:

- Desktop: `Jarvis GUI.lnk`
- Autostart: `Jarvis GUI Autostart.lnk`

## Manuelle Startdateien

- `Jarvis.bat`
- `Start-Jarvis-GUI.bat`
- `Start-Jarvis-GUI.ps1`
- `scripts/start_gui.py`
- `scripts/start_jarvis_gui.py`

## Startlogik

1. Prüft laufende GUI über PID-Datei und Port `8851`.
2. Startet `scripts/start_hud.py`, falls noch nicht aktiv.
3. Öffnet Browser auf `http://127.0.0.1:8851`.
4. `/quiet` startet ohne Browser für Autostart.
