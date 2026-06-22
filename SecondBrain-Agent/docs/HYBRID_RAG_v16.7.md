# SecondBrain OS v16.7 – Hybrid RAG 2.0

## Ziel
v16.7 ergänzt die RAG-Schicht mit hybridem Retrieval.

## Enthalten
- BM25-ähnliche Suche
- Pseudo-Embeddings
- Hybrid Ranking
- Reranking
- Citation Engine
- Context Compression
- Inkrementelles Indexing
- SQLite Persistence

## Befehle
```powershell
python launcher.py rag16-migrate
python launcher.py rag16-seed
python launcher.py rag16-status
python launcher.py rag16-index-text "Demo" "Jarvis nutzt Hybrid RAG."
python launcher.py rag16-bm25 Jarvis
python launcher.py rag16-vector Jarvis
python launcher.py rag16-search "Hybrid RAG"
python launcher.py rag16-answer "Was nutzt Jarvis?"
python launcher.py rag16-sources
python launcher.py rag16-runs
```

## Grenzen
- Embeddings sind deterministische Pseudo-Vektoren.
- Kein echter LLM-Call.
- Kein pgvector.
- BM25 ist vereinfacht.
