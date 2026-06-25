# Delta v30.21 anwenden

1. ZIP im Repository-Root entpacken, vorhandene Dateien überschreiben.
2. Im Ordner `SecondBrain-Agent` ausführen:

```bash
python launcher.py gui-bootstrap
python launcher.py gui-doctor
python launcher.py
```

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\Install-Jarvis-Desktop.ps1
```

Danach kann Jarvis per `Jarvis.bat`, Desktop-Verknüpfung oder `python launcher.py` gestartet werden.
