# SecondBrain OS v16.1 – Database Architecture

## Ziel
v16.1 ersetzt reine JSON-Ablage durch eine relationale Persistence-Schicht.

## Enthalten
- SQLite-kompatible Runtime
- PostgreSQL-ready Architektur
- Core Schema:
  - memories
  - tasks
  - documents
  - events
  - automations
  - embeddings
  - schema_migrations
- Migration Runner
- Repository-nahe Methoden
- pgvector-Migrationsplan

## Befehle
```powershell
python launcher.py db16-health
python launcher.py db16-migrate
python launcher.py db16-migrations
python launcher.py db16-stats
python launcher.py db16-memory-add "Jarvis nutzt PostgreSQL" --kind architecture
python launcher.py db16-memory-search postgresql
python launcher.py db16-task-add "DB testen" --priority high
python launcher.py db16-document-add "Plan" --content "Datenbankplan"
python launcher.py db16-event db.created "{}"
python launcher.py db16-embedding-add memory m1 "0.1,0.2,0.3"
python launcher.py db16-postgres-plan
```

## Grenzen
- Noch SQLite statt echter PostgreSQL-Verbindung.
- pgvector ist als Zielmodell vorbereitet, noch nicht produktiv aktiv.
- Keine Alembic-Dateien, Migration erfolgt intern deterministisch.
