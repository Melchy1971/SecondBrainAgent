# CHANGELOG v17.5 P0

## Schwerpunkt
P0-Härtung der Launcher-/Registry-/Gate-Schicht.

## Änderungen
- `p0-smoke` ergänzt.
- `p0-smoke --write-report` ergänzt.
- Smoke-Report: `runtime/reports/p0_smoke_latest.json`.
- Command-Konfliktprüfung in `ModuleRegistry` ergänzt.
- Kritische Module explizit aus Registry ableitbar.
- `p0-gate` blockiert jetzt doppelt belegte Commands.
- P0-Tests erweitert.

## Validierung
- `python launcher.py --project-root . p0-gate`: PASS.
- `python launcher.py --project-root . p0-smoke --write-report`: PASS.
- `PYTHONPATH=. python -m pytest -q`: 240 passed.
