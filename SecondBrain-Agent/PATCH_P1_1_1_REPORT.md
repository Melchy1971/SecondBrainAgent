# PATCH P1.1.1 — Embedding Provider Abstraction

## Ziel
RAG-Embedding-Schicht von konkreten Provider-Implementierungen entkoppeln.

## Geänderte Dateien
- `secondbrain/rag/providers/base.py`
- `secondbrain/rag/providers/deterministic_provider.py`
- `secondbrain/rag/providers/gemini_provider.py`
- `secondbrain/rag/providers/factory.py`
- `secondbrain/rag/providers/__init__.py`
- `secondbrain/rag/embedding_provider.py`
- `tests/test_p1_1_1_embedding_factory.py`

## Ergebnis
- Einheitliches Provider-Interface
- Typed Provider Config
- Deterministischer Offline-/Test-Provider
- Ollama/OpenAI Factory-Verdrahtung
- Gemini Adapter mit Client-Injection
- Output-Normalisierung und Fehlerhärtung
- Rückwärtskompatibler Importpfad `secondbrain.rag.embedding_provider.EmbeddingProvider`

## Validierung
- `pytest tests/test_p0_3_embedding_providers.py tests/test_p1_1_1_embedding_factory.py -q`
- `11 passed`
