# v30.21 Unified Application Bootstrap

## Ziel

Jarvis soll ohne Parameter über `python launcher.py` oder Windows-Doppelklick starten.

## Änderungen

- `python launcher.py` startet jetzt die GUI statt nur Modulstatus.
- Neuer Alias: `python launcher.py jarvis`.
- Neuer Diagnosebefehl: `python launcher.py gui-bootstrap`.
- Bootstrap erzeugt fehlende `.env` Defaults.
- Bootstrap erzeugt Runtime-/Datenordner.
- Bootstrap schreibt `runtime/reports/bootstrap_v30_21.json`.
- GUI-Start blockiert bei harten Startfehlern.
- Windows-BAT/PowerShell-Startdateien auf Jarvis-Alias aktualisiert.
- Desktop-/Startmenü-Verknüpfungsinstaller aktualisiert.

## Akzeptanz

```bash
python launcher.py gui-bootstrap
python launcher.py gui-doctor
python launcher.py
```
