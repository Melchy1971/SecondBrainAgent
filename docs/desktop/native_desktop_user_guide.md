# Native Desktop User Guide

Start: `python launcher.py native-gui`. Prüfung: `python launcher.py native-voice-app-gate`.

PySide6 ist optional. Fehlt es, bleibt die bestehende native Tkinter-Anwendung verfügbar. Fehlende
Mikrofone, STT-Modelle, Provider oder Datenbanken werden als Degraded Mode angezeigt und dürfen
den Shell-Start nicht verhindern. Push-to-Talk aktiviert nur eine laufende Sitzung; Audiodaten
werden nicht gespeichert. Externe Schreibaktionen erscheinen in Approvals und werden erst nach
einer an Payload und Workspace gebundenen Freigabe ausgeführt.
