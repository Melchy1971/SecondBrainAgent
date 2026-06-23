# PATCH P2.4.1 – Semantic Search Foundation

## Scope

Implemented the desktop semantic search foundation as a delta package.

## Added

- `secondbrain/desktop/search/search_query.py`
- `secondbrain/desktop/search/search_result.py`
- `secondbrain/desktop/search/search_filters.py`
- `secondbrain/desktop/search/search_facets.py`
- `secondbrain/desktop/search/search_history.py`
- `secondbrain/desktop/search/search_state.py`
- `secondbrain/desktop/search/search_events.py`
- `secondbrain/desktop/search/search_persistence.py`
- `secondbrain/desktop/search/search_service.py`
- `tests/desktop/search/test_search_foundation.py`

## Capabilities

- Normalized query model
- In-memory search backend for deterministic desktop tests
- Search result sanitizing to avoid leaking technical metadata
- Workspace/tag/status/source filters
- Facet calculation
- Search history
- JSON persistence for history
- Search state lifecycle
- Event emission for started/completed/failed/history-updated

## Validation

`8 passed in 0.31s`

## Next

P2.4.2 Hybrid Search UI adapter.
