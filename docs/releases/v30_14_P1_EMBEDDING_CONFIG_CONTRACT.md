# v30.14 P1 Embedding Config Contract

## Ziel
Produktions-RAG darf nicht über implizite Default-/Fallback-Konfigurationen laufen.

## Änderungen
- Neuer Config-Contract `secondbrain.p1_embedding_config.v1`.
- Neuer Launcher-Befehl `p1-embedding-config`.
- `provider_from_profile()` nutzt zentrale Config-Auswertung.
- ENV-Unterstützung für:
  - `SECONDBRAIN_EMBEDDING_PROVIDER`
  - `SECONDBRAIN_EMBEDDING_MODEL`
  - `SECONDBRAIN_EMBEDDING_DIMENSIONS`
  - `SECONDBRAIN_OLLAMA_BASE_URL`
  - `SECONDBRAIN_OPENAI_API_KEY_ENV`
  - `SECONDBRAIN_EMBEDDING_ALLOW_FALLBACK`
- Production Config blockiert:
  - lokale Test-Embeddings
  - aktivierten Fallback
  - OpenAI ohne API-Key-ENV
  - ungültige Ollama Base URL
  - unbekannte Provider

## Akzeptanz
```bash
python launcher.py p1-embedding-config --write-report
python launcher.py p1-provider-health --write-report
pytest -q tests/test_v3014_p1_embedding_config_contract.py
```
