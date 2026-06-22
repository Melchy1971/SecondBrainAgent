# SecondBrain-Agent v18.0 P1

## Schwerpunkt
P1 startet nach abgeschlossenem P0-Gate mit produktnäherer RAG-/Memory-Grundlage.

## Ergänzt
- `secondbrain/p1_rag_runtime.py`
- SQLite-basierter lokaler RAG-Index ohne externe Pflichtabhängigkeiten
- deterministisches Chunking
- Tokenisierung und lexikalisches Ranking
- Quellen-/Chunk-Citations
- `p1-rag-status`
- `p1-rag-ingest-text`
- `p1-rag-ingest-file`
- `p1-rag-search`
- `p1-rag-answer`
- `p1-gate`
- P1-Tests

## Produktlogik
P1 baut keine autonome KI-Antwort ohne lokale Evidenz. Antworten enthalten lokale Quellenverweise und Konfidenzscore.

## Grenzen
- Noch keine echten Embeddings
- Noch kein pgvector
- Noch kein LLM-Reranking
- Noch keine GUI-Anbindung
