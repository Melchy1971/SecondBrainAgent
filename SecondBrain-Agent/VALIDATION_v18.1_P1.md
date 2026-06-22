# Validation v18.1 P1

## Commands

```bash
python launcher.py p1-rag-ingest-text "Jarvis indexiert P1 Quellen mit Explainability und Metadaten" --source smoke --title V181
python launcher.py p1-rag-sources
python launcher.py p1-rag-explain Quellen
python launcher.py p1-gate --write-report
PYTHONPATH=. pytest -q
```

## Ergebnis

| Prüfung | Ergebnis |
|---|---:|
| p1-rag-sources | PASS |
| p1-rag-explain | PASS |
| p1-gate | PASS |
| pytest | 258 passed |

## Restrisiko

- RAG nutzt weiterhin deterministisches lokales TF-IDF-Scoring, noch keine echten Embeddings.
- Persistenz ist SQLite-basiert, PostgreSQL/pgvector ist noch nicht produktiv verdrahtet.
- Dokumentparser für PDF/OCR ist noch nicht Teil dieses Pakets.
