# v31.42 Windows Startup

Der native Jarvis-Desktop kann jetzt explizit für den Benutzer-Autostart aktiviert werden:

- `python launcher.py native-startup-status`
- `python launcher.py native-startup-enable`
- `python launcher.py native-startup-disable`

Die Funktion ist standardmäßig deaktiviert, unterstützt nur Windows und schreibt ausschließlich
`JarvisSecondBrain.cmd` in den Startup-Ordner des aktuellen Benutzers. Projekt-, Python- und
Launcher-Pfade werden vollständig gequotet. Aktivierung ist idempotent und Deaktivierung entfernt
nur diese verwaltete Datei.
