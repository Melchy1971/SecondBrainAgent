# Delta v30.31 — Native Command Center

## Ziel

Jarvis erhält eine native Kommandozentrale für Desktop- und Sprachbedienung. Der Web-HUD-Pfad bleibt sekundär. Aktionen werden über einen zentralen Katalog auffindbar, ausführbar, protokolliert und bei Schreibzugriffen abgesichert.

## Neue Befehle

```bash
python launcher.py command-center-status
python launcher.py command-palette --query "index"
python launcher.py command-run "Systemstatus prüfen" --dry-run
python launcher.py command-run "Repariere Index"
python launcher.py command-approvals
python launcher.py command-approval-run <approval_id>
python launcher.py command-approval-reject <approval_id>
python launcher.py command-history
python launcher.py command-center-gui
```

## Neue Dateien

```text
secondbrain/native/__init__.py
secondbrain/native/command_center.py
secondbrain/native/command_center_gui.py
tests/test_v3031_native_command_center.py
docs/releases/v30_31_native_command_center.md
```

## Geänderte Datei

```text
launcher.py
```

## Validierung

```bash
pytest tests/test_v3031_native_command_center.py -q
python launcher.py command-center-status
python launcher.py command-palette --query "index"
python launcher.py command-run "Repariere Index" --dry-run
```

## Risiko

Schreibende Aktionen werden nicht direkt ausgeführt. `rag.reindex` erzeugt zuerst eine Approval-ID und muss explizit bestätigt werden.
