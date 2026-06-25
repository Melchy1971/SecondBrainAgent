# Delta v30.20 anwenden

1. ZIP entpacken.
2. Inhalt aus `SecondBrain-Agent/` in dein Projektverzeichnis `SecondBrain-Agent/` kopieren.
3. Bestehende Dateien überschreiben.
4. Prüfen:

```powershell
python launcher.py gui-doctor
python launcher.py gui-status
python launcher.py gui-open
```

5. Desktop-Verknüpfung neu erstellen:

```powershell
powershell -ExecutionPolicy Bypass -File Install-Jarvis-Desktop.ps1
```

## Wichtig

Alte Verknüpfungen `Jarvis HUD.lnk` können entfernt werden. Neue Zielverknüpfung: `Jarvis GUI.lnk`.
