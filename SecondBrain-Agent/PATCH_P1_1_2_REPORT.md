# PATCH P1.1.2 – Embedding Cache

## Ziel
Provider-/Model-isolierter Embedding-Cache als Read-through-Schicht für RAG.

## Geänderte Dateien
- `secondbrain/rag/cache/__init__.py`
- `secondbrain/rag/cache/cache_repository.py`
- `secondbrain/rag/cache/embedding_cache.py`
- `tests/test_p1_1_2_embedding_cache.py`

## Implementiert
- SHA-256 Cache-Key aus `schema_version + provider + model + normalized_text`
- Whitespace-Normalisierung ohne semantische Textveränderung
- `CachedEmbedding` mit Provenance-Metadaten
- `EmbeddingCacheRepository` Protocol
- `InMemoryEmbeddingCacheRepository` für Tests/Desktop-Modus
- `EmbeddingCacheService` als Read-through Cache
- defensive Copies gegen versehentliche Vector-Mutation
- Cache-Stats: hits, misses, writes, entries, hit_rate
- gezielte Invalidierung pro Provider/Model/Text

## Validierung
- `pytest -q tests/test_p1_1_2_embedding_cache.py`
- Ergebnis: `5 passed in 0.48s`
- `pytest --collect-only -q`
- Ergebnis: `407 tests collected in 1.41s`

## Hinweis
Vollständiger Testlauf wurde gestartet, lief aber im Container in ein Timeout. Der neue Scope ist isoliert grün; Testsammlung ist stabil.
