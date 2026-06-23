# PATCH P1.1.6 - Retrieval Metrics

## Scope
- Added dependency-free RAG retrieval metrics collector.
- Added immutable metrics snapshot export.
- Added latency timers for retrieval, embedding and reranking.
- Added cache hit/miss metrics and cache hit-rate calculation.
- Added context shape metrics: chunks returned and context tokens.
- Added generic counters for pipeline-specific extensions.

## Files
- `secondbrain/rag/metrics.py`
- `tests/test_p1_1_6_retrieval_metrics.py`

## Validation
- Targeted: `6 passed`
- Full suite: `433 passed in 18.94s`

## Implementation Notes
- No external observability dependency introduced.
- Metrics are exportable as dictionaries for logs, dashboards or KPI stores.
- Invalid negative values fail fast with `ValueError`.
- Unknown timer names are captured as generic latency counters.
