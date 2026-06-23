# PATCH P2.4.3 – Search Preview & Highlighting

## Scope

Implemented safe preview generation and query highlighting for desktop semantic search results.

## Added

- `secondbrain/desktop/search/preview.py`
- `tests/desktop/search/test_search_preview.py`

## Changed

- `secondbrain/desktop/search/__init__.py`

## Capabilities

- Bounded snippets with configurable character budget
- Context-window extraction around first query hit
- Query-term extraction with de-duplication
- Deterministic highlight ordering
- HTML-safe highlighted previews by default
- Preview metadata for source, query terms and snippet offset
- Batch preview generation

## Validation

`6 passed in 0.21s`

## Next

P2.4.4 Saved Searches.
