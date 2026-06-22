# SecondBrain-Agent v18.4 P1

## Schwerpunkt
P1 RAG-Produktionshärtung durch Embedding-Abstraktion, lokalen VectorStore und Hybrid Retrieval.

## Änderungen
- `EmbeddingProvider`-Schnittstelle ergänzt.
- `LocalEmbeddingProvider` als deterministische Offline-Fallback-Implementierung ergänzt.
- `OllamaEmbeddingProvider` mit lokalem HTTP-Endpunkt und Fallback ergänzt.
- `OpenAIEmbeddingProvider` als offline-sichere Provider-Grenze ergänzt.
- SQLite-basierter `chunk_embeddings` VectorStore ergänzt.
- automatische Embedding-Erzeugung beim Ingest ergänzt.
- `p1-rag-reindex` ergänzt.
- `p1-embedding-status` ergänzt.
- `p1-rag-vector-search` ergänzt.
- `p1-rag-hybrid-search` ergänzt.
- `p1-retrieval-benchmark` ergänzt.
- `p1-gate` auf `secondbrain.p1_gate.v4` verschärft.
- Index-Validierung prüft fehlende, verwaiste und defekte Embeddings.
- Tests für Embeddings, VectorStore, Hybrid Search, Reindex und Benchmark ergänzt.

## Risikoabbau
- RAG hängt nicht mehr nur an Keyword-Matching.
- Providerwechsel ist gekapselt.
- Offline-Tests bleiben stabil ohne API-Key/Ollama-Verfügbarkeit.
- VectorStore-Artefakte werden im Gate geprüft.
