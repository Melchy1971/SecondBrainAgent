# v30.63 — Vollstaendige pgvector-Unterstuetzung

Baut auf v30.62 (Data Access). **Keine Breaking Changes**: die bestehenden
`PgVectorRepository.upsert/search`, `VectorIndexManager` und `VectorRecord/VectorSearchResult`
bleiben unveraendert; alles Neue ist additiv.

## Neu
- `storage/vector_index.py` — DDL-Builder fuer **HNSW** (`m`, `ef_construction`) und **IVFFLAT** (`lists`),
  je Metrik `cosine`/`l2`/`ip` (Operatoren `<=>`/`<->`/`<#>`).
- `storage/vector_store.py` — `VectorStore`-Protokoll mit zwei Backends:
  - `SqliteVectorStore` (stdlib, Python-Similarity) fuer Development/Tests — kein pgvector noetig.
  - `PgVectorStore` (Produktion) — **wrappt das bestehende `PgVectorRepository`** (Single-Search
    unveraendert) und ergaenzt Batch-Insert, Reindex (HNSW/IVFFLAT), alternative Metriken und EXPLAIN.
  - `search(...)` liefert den bestehenden `VectorSearchResult`; Cosine-Score = `1 - distance` (identisch).
- `storage/vector_migrate.py` — `migrate_vectors(source, target, batch_size)`: **SQLite -> PostgreSQL**
  in Batches.
- `storage/vector_benchmark.py` — `run_benchmark(...)`: reproduzierbarer Batch-Insert + Query-Latenz
  (p50/p95/mean, inserts/sec), backend-agnostisch.
- **Explain**: `store.explain(query)` -> PostgreSQL `EXPLAIN`/Plan bzw. sqlite `EXPLAIN QUERY PLAN`.

## Launcher (Python 3.11+, PG mit requirements-db.txt + pgvector-Extension)
```
python launcher.py vector-benchmark --count 5000 --dim 384 --queries 50
python launcher.py vector-reindex --method hnsw --metric cosine     # oder --method ivfflat
python launcher.py vector-explain --dim 384 --metric cosine
python launcher.py vector-migrate --from sqlite:///runtime/dev.sqlite3   # Ziel = aktuelle DATABASE_URL
```

## Vector Column / Index
Die Spalte `embedding vector` + Basis-Index kommen aus Migration `002_pgvector_embeddings.sql`;
HNSW/IVFFLAT werden zur Laufzeit ueber `vector-reindex` bzw. `PgVectorStore.reindex()` erzeugt
(IF NOT EXISTS, idempotent). IVFFLAT ist optional (Parameter `lists`).

## Tests
`tests/storage/` (vector-Anteil): Index-DDL, Store (Cosine/L2/IP, Filter, Upsert-Konflikt, Explain,
Reindex-Noop), Migrate (Batches, leer, Validierung), Benchmark (deterministisch, Struktur),
**Kompatibilitaets-Guard** (`test_vector_compat.py`: PgVectorRepository/Index/Modelle unveraendert).
`test_pgvector_integration.py` laeuft nur mit `TEST_DATABASE_URL` (+ SQLAlchemy/pgvector), sonst skip.

## Grenzen (ehrlich)
Die Sandbox hat kein PostgreSQL/pgvector — die echte ANN-Performance (HNSW/IVFFLAT-Recall/Latenz) und
das EXPLAIN-ANALYZE des Index-Scans sind nur am Live-System valide. Der SQLite-Dev-Pfad rechnet
Similarity linear in Python (korrekt, aber kein ANN); er dient Entwicklung und deterministischen Tests.
