# Apply Delta v30.15 P1 Embedding Dimension Contract

## Inhalt

Dieses Delta baut auf v30.14 auf.

Geänderte/neue Dateien:

```text
SecondBrain-Agent/secondbrain/p1_embeddings.py
SecondBrain-Agent/secondbrain/p1_embedding_config.py
SecondBrain-Agent/secondbrain/p1_provider_health.py
SecondBrain-Agent/tests/test_v3015_p1_embedding_dimension_contract.py
SecondBrain-Agent/docs/releases/v30_15_P1_EMBEDDING_DIMENSION_CONTRACT.md
SecondBrain-Agent/docs/09_MASTERPLAN_STATUS.json
```

## Anwendung

ZIP im Repository-Root entpacken und Dateien überschreiben.

## Validierung

```bash
cd SecondBrain-Agent
pytest -q tests/test_v3014_p1_embedding_config_contract.py tests/test_v3015_p1_embedding_dimension_contract.py tests/test_v3012_p1_provider_health_gate.py
pytest --collect-only -q
```

Erwartung:

```text
15 PASS
1006 tests collected
```

## Akzeptanzlogik

- `provider_from_profile()` erzwingt Dimension-Vertrag für OpenAI/Ollama.
- OpenAI/Ollama blockieren bei tatsächlicher Dimension != konfigurierter Dimension.
- Provider Health blockiert `embedding_dimension_contract_failed`.
- Provider-Defaults verhindern falsche 64-Dimensionen für produktive Provider.
