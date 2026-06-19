# v9.6 Production Ready Guide

## Ziel

v9.6 macht SecondBrain OS robuster für den täglichen Einsatz.

## Neue Befehle

```powershell
python scripts\installer_check_v96.py
python scripts\create_update_backup_v96.py
python scripts\settings_report_v96.py
python scripts\production_ready_gate_v96.py
python scripts\update_preflight_v96.py
```

## Empfohlene Routine vor Updates

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python scripts\update_preflight_v96.py
```

## Menü

```powershell
python scripts\menu.py
```

Wichtige Optionen:

```text
3 = Installer Check v9.6
4 = Update Backup v9.6
5 = Settings Report v9.6
6 = Production Ready Gate v9.6
7 = Update Preflight v9.6
```
