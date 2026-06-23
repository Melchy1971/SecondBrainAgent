# PATCH P1.1.4 — Reranker Layer

## Ziel
Produktionssichere Reranker-Schicht für RAG Retrieval.

## Geänderte Dateien
- `secondbrain/rag/reranker.py`
- `tests/test_p1_1_4_reranker.py`

## Implementiert
- `RerankScorer` Protocol
- `RerankerConfig`
- `KeywordOverlapScorer` als deterministischer Offline-Fallback
- `Reranker` mit Fail-Open/Fail-Closed Verhalten
- stabile Sortierung nach Score, Document-ID, Chunk-ID
- Metadaten: `rerank_score`, `pre_rerank_score`, `reranker`

## Validierung
- `tests/test_p1_1_4_reranker.py`: 6 passed
- vollständiger Testlauf: 419 passed in 17.79s

## Risiko
- Externer Cross-Encoder ist noch nicht angebunden.
- Aktuelle Implementierung liefert robuste Schicht + Fallback, nicht maximale semantische Qualität.
