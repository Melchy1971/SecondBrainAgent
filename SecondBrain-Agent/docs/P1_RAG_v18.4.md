# P1 RAG v18.4

## Zielbild
Der lokale RAG-Core besitzt ab v18.4 eine Provider-Abstraktion für Embeddings, einen persistenten VectorStore und eine Hybrid-Retrieval-Schicht.

## Komponenten

### EmbeddingProvider
Einheitliche Schnittstelle für lokale und externe Embedding-Provider.

Implementierungen:
- `LocalEmbeddingProvider`: deterministisch, offline, testbar.
- `OllamaEmbeddingProvider`: vorbereitet für lokale Ollama-Embeddings mit Fallback.
- `OpenAIEmbeddingProvider`: Provider-Grenze für spätere SDK-Verdrahtung mit Offline-Fallback.

### VectorStore
Persistiert Chunk-Vektoren in SQLite-Tabelle `chunk_embeddings`.

Prüfungen:
- fehlende Embeddings
- defekte Vektor-JSONs
- Dimensionskonflikte
- verwaiste Embeddings

### Hybrid Retrieval
Kombiniert:
- Keyword-TFIDF
- Vektorähnlichkeit

Ausgabe enthält:
- `keyword_score`
- `vector_score`
- `hybrid_score`
- `rank_sources`

## Gate v4
`p1-gate` prüft zusätzlich:
- Embedding Provider verfügbar
- Embeddings konsistent
- Hybrid Search lauffähig
- Retrieval Benchmark verfügbar

## Grenzen
- `LocalEmbeddingProvider` ist kein echtes semantisches Modell.
- Ollama/OpenAI sind als Schnittstellen vorbereitet; produktive Modellqualität hängt vom konfigurierten Provider ab.
- pgvector ist noch nicht produktiv verdrahtet; SQLite bleibt lokaler P1-Store.
