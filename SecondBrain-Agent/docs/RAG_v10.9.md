# SecondBrain OS v10.9 – Advanced RAG Foundation

## Zweck

v10.9 ergänzt eine lokale RAG-Grundschicht für Markdown- und Textbestände.

## Datenfluss

```text
Vault
↓
Document Loader
↓
Markdown Section Splitter
↓
Chunk Optimizer
↓
Knowledge Scoring
↓
Hybrid Search
↓
Citation Answer
```

## CLI

```powershell
python launcher.py rag-index
python launcher.py rag-search "Projektplan Connector" --limit 5
python launcher.py rag-answer "Was ist der aktuelle Jarvis-Plan?"
python launcher.py rag-answer "Was ist der aktuelle Jarvis-Plan?" --write
```

## Scoring

| Faktor | Wirkung |
|---|---|
| lexical_score | direkte Query-Treffer |
| semantic_score | normalisierte Token-Überdeckung |
| quality_score | Struktur, Länge, Informationsdichte |
| trust_score | Quelltyp/Ordnergewichtung |
| freshness_score | Aktualität nach Dateiänderung |

## Grenzen

- Keine externen Embeddings.
- Keine Vektor-DB-Abhängigkeit.
- Bewusst offline-fähig.
- Geeignet als robuste Foundation vor pgvector/Qdrant/FAISS.
