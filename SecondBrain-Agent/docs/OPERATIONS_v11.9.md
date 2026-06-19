# SecondBrain OS v11.9 – Operations & Release Layer

## Ziel

v11.9 ergänzt den produktionsnahen Betriebsrahmen vor v12.0. Der Fokus liegt auf Backup, Release-Gates, Migrationskontrolle und Health Reports.

## Neue Launcher-Befehle

```powershell
python launcher.py ops-status
python launcher.py ops-backup --label pre_v12
python launcher.py ops-backups
python launcher.py ops-backup-verify <BACKUP_ID_ODER_PFAD>
python launcher.py ops-release-gate
python launcher.py ops-health-report
python launcher.py ops-migration-plan --target-version 12.0
python launcher.py ops-migration-mark v119_backup_gate --note "Backup validiert"
python launcher.py ops-restore-plan <BACKUP_ID_ODER_PFAD>
python launcher.py ops-restore <BACKUP_ID_ODER_PFAD> --target-dir H:\SecondBrainAgent\restore-test
```

## Restore-Verhalten

Restore überschreibt das aktive Projekt nicht. Backups werden in einen separaten Zielordner extrahiert. Das reduziert Risiko bei fehlerhaften Releases.

## Release Gate

Prüft Mindeststruktur:

- `launcher.py`
- `requirements.txt`
- `secondbrain/`
- schreibbares Runtime-Verzeichnis
- schreibbares Backup-Verzeichnis
- Tests/Doku/Config als Warnungen

Statuslogik:

- `PASS`: keine Fehler, keine Warnungen
- `CONDITIONAL_PASS`: keine Fehler, aber Warnungen
- `FAIL`: mindestens ein harter Fehler

## Upgrade-Pfad nach v12.0

Vor v12.0 ausführen:

```powershell
python launcher.py ops-backup --label before_v12
python launcher.py ops-release-gate
python launcher.py ops-health-report
python launcher.py ops-migration-plan --target-version 12.0
```
