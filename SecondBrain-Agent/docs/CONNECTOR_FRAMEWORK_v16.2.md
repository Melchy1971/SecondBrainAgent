# SecondBrain OS v16.2 – Connector Framework

## Ziel
v16.2 liefert ein einheitliches Connector Framework mit Datenbankpersistenz.

## Connectoren
- Gmail
- Google Calendar
- Google Drive
- GitHub
- Obsidian
- Paperless-ngx

## Enthalten
- Connector Registry
- Enable/Disable
- OAuth-/Token-Template
- Delta Cursor
- Sync Runs
- Connector Items
- Dead Letter Queue
- SQLite Persistence
- PostgreSQL-kompatible Zielstruktur

## Befehle
```powershell
python launcher.py conn16-migrate
python launcher.py conn16-status
python launcher.py conn16-list
python launcher.py conn16-enable gmail
python launcher.py conn16-oauth-template gmail
python launcher.py conn16-token-store gmail demo-token
python launcher.py conn16-sync gmail
python launcher.py conn16-sync-all
python launcher.py conn16-runs
python launcher.py conn16-items --connector-id gmail
python launcher.py conn16-dlq
```

## Grenzen
- API Calls sind noch Demo-Fetcher.
- OAuth ist Template/Token-Ref, kein echter Browser Flow.
- Tokens werden nicht produktiv verschlüsselt.
- Echter API-Ausbau folgt connector-spezifisch.
