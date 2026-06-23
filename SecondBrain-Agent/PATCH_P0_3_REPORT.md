# PATCH P0.3 - Embedding Provider Runtime Repair

## Ziel
Harte Laufzeitabbrüche durch `NotImplementedError` in den produktionsrelevanten RAG-Embedding-Providern entfernen.

## Geänderte Dateien
- `secondbrain/rag/providers/ollama_http_client.py`
- `secondbrain/rag/providers/openai_http_client.py`
- `secondbrain/rag/providers/ollama_embedding_provider.py`
- `secondbrain/rag/providers/openai_embedding_provider.py`
- `tests/test_p0_3_embedding_providers.py`

## Implementierung
- Dependency-freie HTTP-Clients mit `urllib`.
- Ollama-Unterstützung für:
  - `/api/embed`
  - Fallback `/api/embeddings`
- OpenAI-kompatible Embeddings über `/v1/embeddings`.
- Explizite Fehlerklassen:
  - `OllamaEmbeddingError`
  - `OpenAIEmbeddingError`
- Provider delegieren an injizierbare Clients.
- Testbarkeit ohne Netzwerk durch Fake-Client-Injektion.
- Leere Batches liefern `[]` ohne Netzwerkzugriff.
- Fehlender OpenAI API Key endet kontrolliert statt implizit zu scheitern.

## Validierung
Targeted Testlauf:

```bash
python -m pytest -q tests/test_p0_3_embedding_providers.py tests/test_p0_2_package_repair.py tests/test_v193_p1_retrieval_maturity.py
```

Ergebnis:

```text
13 passed in 0.70s
```

Zusätzlicher Gesamt-Testlauf wurde gestartet. Die Suite lief bis mindestens 49 Prozent ohne Fehler, wurde jedoch durch die Ausführungszeit des Containers abgebrochen. Kein neuer Fehler wurde bis zum Abbruch sichtbar.

## Restlücken nach P0.3
- PgVector Repository bleibt Scaffold.
- Connector Framework nutzt weiterhin Fake-Fetch in `connector_framework/runtime.py`.
- Dokumentenverständnis nutzt weiterhin PDF-Stub.
- Doku-Versionen bleiben inkonsistent.
