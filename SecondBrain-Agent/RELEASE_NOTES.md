# SecondBrain-Agent Release Notes

Aktueller dokumentierter Stand: v30.21 Unified Application Bootstrap.

## v30.21 Unified Application Bootstrap

- `python launcher.py` startet Jarvis direkt.
- `python launcher.py jarvis` ist der explizite Alias.
- `python launcher.py gui-bootstrap` erzeugt fehlende lokale Defaults und Runtime-Ordner.
- Bootstrap-Report: `runtime/reports/bootstrap_v30_21.json`.
- Windows-Startdateien und Shortcut-Installer zeigen auf den Jarvis-Launcher.

## v30.20 GUI Startup Surface

- GUI-Kommandos vereinheitlicht: `gui`, `gui-start`, `gui-open`, `gui-status`, `gui-doctor`, `gui-shortcuts`.
- `desktop-gui` und `desktop16-gui` bleiben kompatible Startpfade.
- `Jarvis.bat` nutzt den Launcher statt interner Skripte.

## v30.19 P1 GUI Surface Update

- P1-/RAG-nahe GUI-Flaechen fuer Runtime-Status, Import, Vector Index und Production Gate dokumentiert.
- GUI-Status wurde im Masterplan auf P1 Runtime Surface aktualisiert.

## Relevante aktuelle Artefakte

- `docs/START_GUI.md`
- `docs/releases/v30_19_P1_GUI_SURFACE_UPDATE.md`
- `docs/releases/v30_20_GUI_STARTUP_SURFACE.md`
- `docs/releases/v30_21_UNIFIED_APPLICATION_BOOTSTRAP.md`
- `docs/09_MASTERPLAN_STATUS.json`
