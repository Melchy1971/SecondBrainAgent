# Historischer Patch-Hinweis

Dieses Dokument ist nur noch ein Archivhinweis fuer alte v9-Patchpakete.

Aktuelle Installation und Startbefehle stehen hier:

- `README.md`
- `INSTALLATION_BEGINNER.md`
- `docs/README.md`
- `docs/04_STARTBEFEHLE.md`

Aktueller Stand: v30.45 Native Desktop Integration.

## v30.45

- `python launcher.py` und `python launcher.py desktop` starten dieselbe native Desktop-Shell.
- Gemeinsamer `ApplicationState`, zentrale Navigation, Toolbar und Statusleiste.
- Dashboard, Workspace, Chat, Document Explorer, Memory Explorer, Agent Control,
  Voice Control, Command Center, Job Queue, Notification Center, Settings Center,
  Theme Center und Update Center sind ueber die Shell erreichbar.
- Bestehende Modulstarts und Diagnosekommandos bleiben erhalten.


## v30.25

Native Desktop ist jetzt der Primaerstart. Web-HUD bleibt nur noch Legacy-Kompatibilitaet. Deutsche Sprachsteuerung ist in `secondbrain.desktop_native.voice_de` verdrahtet.
