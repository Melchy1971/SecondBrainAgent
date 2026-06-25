# SecondBrainAgent Delta v30.8 — P1 Migration Runner + Store Search Hardening

## Apply
Copy the contained `SecondBrain-Agent/` files over the existing repository root after v30.7.

## Added/Changed
- Added `secondbrain/p1_rag_migration.py`.
- Added launcher command `p1-rag-migrate-postgres`.
- Registered `p1-rag-migrate-postgres` in ModuleRegistry.
- Changed `P1RagRuntime.vector_search()` to use `RagStore.vector_search()` instead of direct SQLite reads.
- Hardened P1 gate to check selected RagStore availability.
- Hardened `pgvector_live_check()` to block when `vector` extension is missing.
- Updated `docs/09_MASTERPLAN_STATUS.json` to v30.8.
- Added focused tests for migration runner, command registration, extension-missing live check, and store-backed vector search.

## Validation
```bash
python -m pytest --collect-only -q
# 978 tests collected

python -m pytest -q \
  tests/test_v308_p1_migration_store_hardening.py \
  tests/test_v307_p1_store_runtime_bridge.py \
  tests/test_v193_p1_store_backed_ingest.py \
  tests/test_v180_p1_rag.py
# 20 passed
```

## New commands
```bash
python launcher.py p1-rag-migrate-postgres --write-report
python launcher.py p1-rag-migrate-postgres --apply --write-report
python launcher.py p1-rag-migrate-postgres --allow-non-pgvector --write-report
```

## Remaining external validation
- `pytest -q` full run outside sandbox timeout.
- `python launcher.py p3-pgvector-readiness --live --apply --write-report` against VPS.
- `python launcher.py p1-rag-migrate-postgres --apply --write-report` against VPS.
