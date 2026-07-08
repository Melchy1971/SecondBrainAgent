# v30.62 — Production Data Access: PostgreSQL-first, SQLite dev-only

## Analyse (Ist-Zustand)
Es existierte bereits eine v30.1-Schicht: `DatabaseConfig.from_env` (liest DATABASE_URL /
SECOND_BRAIN_DATABASE_URL + Pool-Parameter), `Database` (SQLAlchemy-Engine mit Connection-Pool:
pool_size/max_overflow/pool_recycle/pool_pre_ping/statement_timeout, `session()`-Transaktion),
`BaseRepository`/`RepositoryResult`, `TransactionManager`, `DatabaseHealthcheck`, 6 SQL-Migrationen.
Gemischt genutzt: SQLAlchemy **und** rohes sqlite3. Es fehlten: Retry, Startup-Validation,
Migration-Runner, Dev/Prod-Trennung, kontrollierter Fallback.

## Neu (additiv, bestehende APIs unveraendert)
- `storage/db_policy.py` — `resolve()` klassifiziert DATABASE_URL, erzwingt: **PostgreSQL = Produktion,
  SQLite = nur Development**, Fallback nur bei `SECOND_BRAIN_ALLOW_SQLITE_FALLBACK=1`. Fehlende/ungueltige
  DB -> `DatabaseStartupError`.
- `storage/db_retry.py` — `RetryPolicy` + `run_with_retry` fuer transiente Fehler (OperationalError,
  Disconnect, Timeout; per Typname erkannt, kein Treiber-Import).
- `storage/db_executor.py` — backend-agnostischer Executor: `SqliteExecutor` (stdlib, dev/test,
  echte atomare Transaktionen inkl. DDL-Rollback) und `SqlAlchemyExecutor` (Produktion, lazy).
- `storage/migration_runner.py` — wendet `migrations/NNN_*.sql` geordnet an, trackt `schema_migrations`,
  idempotent, atomarer Rollback bei fehlerhafter Migration.
- `storage/db_startup.py` — `validate_and_connect()`: aufloesen -> verbinden (mit Retry) -> **sauber
  blockieren**; SQLite-Fallback nur per Flag. Dependency-injizierbar (testbar ohne PG/SQLAlchemy).
- `storage/db_provider.py` — Facade: `migrate()`, `health()`, `repositories()` (bindet die bestehenden
  SQLAlchemy-Repos an die validierte Produktions-DB).

## Kontrakt
- Quelle: `DATABASE_URL` (oder `SECOND_BRAIN_DATABASE_URL`).
- `SECOND_BRAIN_ENV=production` (Default) + kein/kein-PG-URL + kein Flag  -> **Blockade** (Exit 3).
- `SECOND_BRAIN_ALLOW_SQLITE_FALLBACK=1` -> SQLite-Fallback erlaubt (Dev).
- Pool/Transaktionen/Healthcheck bleiben die bestehenden v30.1-APIs.

## Launcher (Python 3.11+, mit requirements-db.txt)
```
python launcher.py db-validate    # aufloesen + verbinden; Exit!=0 bei fehlender DB
python launcher.py db-status       # Health + Migrationsstatus
python launcher.py db-migrate      # ausstehende Migrationen anwenden
```

## Tests
`tests/storage/` (24 passed, 1 skipped):
- Policy (Dialekt, Dev/Prod, Fallback-Gating, Blockaden), Retry (transient/permanent/Backoff),
  Executor (Transaktion + DDL-Rollback, Datei-Persistenz), Migration-Runner (Reihenfolge, idempotent,
  Rollback), Startup (verbunden / blockiert / Flag-Fallback).
- `test_pg_integration.py`: echter PostgreSQL-Lauf nur mit gesetztem `TEST_DATABASE_URL` (+ SQLAlchemy),
  sonst uebersprungen. Die Sandbox hat kein PG/SQLAlchemy -> echte Abnahme laeuft auf deiner Maschine.

## Grenzen (ehrlich)
- Migrations-SQL-Splitting ist naiv (';'); komplexe PG-Bodies (Dollar-Quoting/Funktionen) brauchen ggf.
  einen robusteren Splitter oder Ein-Statement-Migrationen.
- `repositories()` erfordert den SQLAlchemy/PostgreSQL-Pfad (Produktion).
