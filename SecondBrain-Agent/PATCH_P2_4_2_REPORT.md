# PATCH P2.4.2 – Hybrid Search UI Integration

## Scope

Implemented the desktop adapter layer between the Search UI model and the RAG hybrid retrieval pipeline.

## Added

- `secondbrain/desktop/search/hybrid_search_ui.py`
- `tests/desktop/search/test_hybrid_search_ui.py`

## Changed

- `secondbrain/desktop/search/__init__.py`

## Capabilities

- Configurable vector/BM25 weighting
- Normalized hybrid score calculation
- Candidate coercion from RAG objects, search results, or dictionaries
- Score-breakdown metadata for transparent UI display
- Limit/offset handling with candidate over-fetching
- SearchService compatibility through `HybridSearchBackendAdapter`

## Validation

`14 passed in 0.26s`

## Next

P2.4.3 Search Preview & Highlighting.
