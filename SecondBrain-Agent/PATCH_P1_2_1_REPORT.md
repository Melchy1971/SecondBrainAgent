# PATCH P1.2.1 - Connector Incremental Sync Runtime

## Ziel
Connector-Sync aus Stub-/Diff-Logik in eine robuste Laufzeitstruktur überführen.

## Geliefert
- `secondbrain/connectors/sync_state.py`
  - SyncStatus
  - SyncCursor
  - SyncIssue
  - SyncRunResult
- `secondbrain/connectors/cursor_store.py`
  - CursorStore Protocol
  - InMemoryCursorStore
  - JsonCursorStore
- `secondbrain/connectors/incremental_runner.py`
  - FetchBatch
  - FetchedItem
  - IncrementalConnector Protocol
  - IncrementalSyncRunner
- `tests/test_p1_2_1_connector_incremental_runner.py`

## Wirkung
- Cursor-State explizit und persistierbar
- Fatal Fetch Errors committen keinen neuen Cursor
- Handler-Fehler werden pro Item isoliert
- Partial-Success möglich
- Batch-Limits verhindern Endlossyncs

## Validierung
- Vollständiger Testlauf: siehe Antwort
