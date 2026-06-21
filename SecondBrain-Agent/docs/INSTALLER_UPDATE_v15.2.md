# SecondBrain OS v15.2 – Installer & Update Layer

## Komponenten
- Release Manifest
- Config Validator
- Portable Installer Plan
- Backup Before Update
- Update Check
- Update Plan
- Simulated Update Run
- Rollback Plan

## Befehle
```powershell
python launcher.py install-status
python launcher.py install-manifest
python launcher.py install-manifest-create --version 15.2
python launcher.py install-validate
python launcher.py install-portable-plan H:\SecondBrainAgent
python launcher.py update-check --current-version 15.1
python launcher.py update-plan --current-version 15.1
python launcher.py update-run --current-version 15.1
python launcher.py update-backups
python launcher.py rollback-plan <BACKUP_ID>
```

## Grenzen
- Update ist simuliert.
- Keine echte Dateiüberschreibung.
- Kein MSI/EXE Builder.
- Kein Remote-Update-Feed.
