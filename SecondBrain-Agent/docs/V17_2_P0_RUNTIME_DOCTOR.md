# v17.2 P0 Runtime Doctor

## Ziel
P0 wird von reiner Modul-Existenz auf prüfbare Betriebsfähigkeit erweitert.

## Neue Befehle

```bash
python launcher.py command-index
python launcher.py p0-doctor
python launcher.py --project-root . p0-doctor
python launcher.py module-status desktop
python launcher.py module-health desktop
```

## `p0-doctor`
Prüft:
- zentrale Konfigurationsdateien
- Module Registry
- Import Health
- Runtime Health
- Event Bus Schreibfähigkeit

Erzeugt zusätzlich ein Event:
- Topic: `runtime.p0_doctor`
- Ablage: `runtime/events_v121/events.jsonl`

## Relevanz
Der Doctor ist das neue Minimal-Gate für P0-Integration. Ein Modul gilt nicht mehr als vorhanden, nur weil Dateien existieren. Es muss importierbar sein, einen Status liefern und in die zentrale Runtime-Diagnose passen.

## Grenzen
Noch nicht gelöst:
- Start/Stop-Orchestrierung
- produktive Datenbank
- produktive Secrets
- echte OAuth-Connectoren
- GUI-Control-Center
