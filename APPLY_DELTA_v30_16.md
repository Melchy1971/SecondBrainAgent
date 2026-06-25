# Apply Delta v30.16 P1 Embedding HTTP Provider Boundary

## Inhalt

- `SecondBrain-Agent/secondbrain/p1_embeddings.py`
- `SecondBrain-Agent/secondbrain/p1_embedding_config.py`
- `SecondBrain-Agent/tests/test_v3016_p1_embedding_http_provider.py`
- `SecondBrain-Agent/docs/09_MASTERPLAN_STATUS.json`
- `SecondBrain-Agent/docs/releases/v30_16_P1_EMBEDDING_HTTP_PROVIDER_BOUNDARY.md`

## Anwenden

ZIP im Repo-Root entpacken und vorhandene Dateien überschreiben.

```bash
cd SecondBrain-Agent
pytest -q tests/test_v3016_p1_embedding_http_provider.py tests/test_v3015_p1_embedding_dimension_contract.py tests/test_v3014_p1_embedding_config_contract.py
pytest --collect-only -q
```

## Erwartung

- Fokus-Suite: `13 PASS`
- Collection: `1009 tests collected`

## ENV-Beispiel OpenAI

```bash
set SECONDBRAIN_EMBEDDING_PROVIDER=openai
set SECONDBRAIN_EMBEDDING_MODEL=text-embedding-3-small
set SECONDBRAIN_EMBEDDING_DIMENSIONS=1536
set SECONDBRAIN_EMBEDDING_TIMEOUT_SECONDS=10
set OPENAI_API_KEY=<key>
python launcher.py p1-provider-health --write-report
```

## ENV-Beispiel Ollama

```bash
set SECONDBRAIN_EMBEDDING_PROVIDER=ollama
set SECONDBRAIN_EMBEDDING_MODEL=nomic-embed-text
set SECONDBRAIN_EMBEDDING_DIMENSIONS=768
set SECONDBRAIN_OLLAMA_BASE_URL=http://localhost:11434
set SECONDBRAIN_EMBEDDING_TIMEOUT_SECONDS=10
python launcher.py p1-provider-health --write-report
```
