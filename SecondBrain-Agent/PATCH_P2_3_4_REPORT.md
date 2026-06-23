# PATCH P2.3.4 — Bulk Workflow Engine

## Scope
- Adds bulk document workflow engine for the desktop document center.
- Adds FIFO queue, job model, executor, history, event sink, rollback manager.
- Supports archive, delete, reindex, move workspace, add tags, remove tags, export metadata.
- Adds item-level failure isolation and partial-failure state.
- Adds rollback metadata for destructive operations.

## Changed / Added Files
- `secondbrain/desktop/documents/bulk/bulk_state.py`
- `secondbrain/desktop/documents/bulk/bulk_events.py`
- `secondbrain/desktop/documents/bulk/bulk_job.py`
- `secondbrain/desktop/documents/bulk/bulk_queue.py`
- `secondbrain/desktop/documents/bulk/bulk_history.py`
- `secondbrain/desktop/documents/bulk/bulk_executor.py`
- `secondbrain/desktop/documents/bulk/bulk_engine.py`
- `secondbrain/desktop/documents/bulk/rollback_manager.py`
- `secondbrain/desktop/documents/bulk/__init__.py`
- `tests/desktop/documents/bulk/test_bulk_workflow.py`

## Validation
- Command: `python -m pytest -q`
- Result: `11 passed in 0.32s`

## Release Impact
- Document Center now supports validated multi-document operations.
- Bulk execution is deterministic and does not abort the full job on single item failure.
- Rollback snapshots are available for restore workflows.
