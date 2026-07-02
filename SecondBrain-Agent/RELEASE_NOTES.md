# Release Notes v30.45 - Native Desktop Integration

## Ergebnis

Die vorhandenen nativen Module laufen unter einer gemeinsamen Desktop-Shell. Der
Standardstart und der Alias `desktop` verwenden denselben Startpfad.

## Neu

- Zentrales, UI-unabhaengiges `ApplicationState`-Modell.
- Gemeinsame Navigation, Toolbar und Statusleiste.
- Dashboard, Workspace, Chat, Document Explorer, Memory Explorer, Agent Control,
  Voice Control, Command Center, Job Queue, Notification Center, Settings Center,
  Theme Center und Update Center sind zentral eingebunden.
- Modulfehler werden in der Shell isoliert angezeigt und beenden nicht die Anwendung.
- Alle bisherigen nativen Einzelstarts bleiben unveraendert.

## Start

```powershell
python launcher.py
python launcher.py desktop
```

## Validierung

```powershell
python -m compileall .
pytest -q
```

## Risiko

- Die Anwendung bleibt eine lokale Tkinter-App und ist keine kompilierte EXE.
- Optionale Voice- und Provider-Funktionen benoetigen weiterhin ihre lokalen Abhaengigkeiten.
