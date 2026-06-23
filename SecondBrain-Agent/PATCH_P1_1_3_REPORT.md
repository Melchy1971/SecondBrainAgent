# PATCH P1.1.3 — Hybrid Search

## Ziel
Produktionsnähere Retrieval-Schicht für RAG durch kombinierte Vektor- und BM25-Suche.

## Änderungen

### Neu
- `secondbrain/rag/retrieval/__init__.py`
- `secondbrain/rag/retrieval/score_fusion.py`
- `secondbrain/rag/retrieval/vector_search.py`
- `secondbrain/rag/retrieval/bm25_search.py`
- `secondbrain/rag/retrieval/hybrid_search.py`
- `tests/test_p1_1_3_hybrid_search.py`

## Funktionsumfang
- Kanonisches `SearchResult`-Modell
- Score-Normalisierung auf 0..1
- gewichtete Score-Fusion
- deterministisches Tie-Breaking
- Dependency-freie BM25-Suche
- Dependency-freie In-Memory-Vector-Search
- HybridSearch-Orchestrierung
- Query-Embedding über Provider-Interface
- Edge-Case-Behandlung für leere Queries und Limits <= 0

## Validierung

```text
413 passed in 19.37s
```

## Bewertung
P1.1.3 abgeschlossen. Nächster logischer Schritt: P1.1.4 Reranking.
