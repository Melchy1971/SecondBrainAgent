# SecondBrainAgent Delta v30.7 — P1 Runtime Store Bridge

## Ziel
P1RagRuntime darf nicht mehr hart am lokalen SQLite-Pfad hängen, sobald pgvector über Konfiguration/ENV aktiv ist.

## Enthaltene Änderungen
- `secondbrain/p1_rag_runtime.py`
  - nutzt `create_rag_store(...)` statt direkter `SQLiteRagStore`-Instanz
  - Status, Sources, Validation, Reindex und Chunk-Lesen laufen über RagStore-Kontrakt
  - Dokument-Payload-Löschung läuft über Store-Kontrakt
- `secondbrain/p3_rag_store.py`
  - erweitert den RagStore-Kontrakt um Delete, Chunk-Snapshot, Embedding-Summary und Validation-Snapshot
  - implementiert diese Methoden für SQLite
  - implementiert diese Methoden für PgVector Live Store
- `tests/test_v307_p1_store_runtime_bridge.py`
  - validiert Store-Auswahl
  - validiert store-backed Validation
  - validiert DSN-Redaction und PgVector-Auswahl
- `docs/09_MASTERPLAN_STATUS.json`
  - Status und Blocker aktualisiert

## Anwendung
ZIP-Inhalt ins Repo-Root kopieren und vorhandene Dateien überschreiben.

## Validierung
```bash
cd SecondBrain-Agent
python -m pytest --collect-only -q
python -m pytest -q tests/test_v180_p1_rag.py tests/test_v181_p1_rag_hardening.py tests/test_v193_p1_store_backed_ingest.py tests/test_v307_p1_store_runtime_bridge.py tests/test_v301_postgresql_production.py tests/test_v302_pgvector_production.py
```

## Erwartet
- 973 Tests sammelbar
- Fokus-Suite: 27 PASS

## Noch offen
- Vollständiger `pytest -q` Lauf außerhalb Sandbox-Timeout
- Live-VPS-Validierung mit PostgreSQL/pgvector
- SQLite→PostgreSQL Migration Runner
