# APPLY DELTA v30.14 — P1 Embedding Config Contract

## Inhalt
- `secondbrain/p1_embedding_config.py`
- `secondbrain/p1_embeddings.py`
- `secondbrain/p1_provider_health.py`
- `launcher.py`
- `secondbrain/module_registry.py`
- `tests/test_v3014_p1_embedding_config_contract.py`
- `docs/releases/v30_14_P1_EMBEDDING_CONFIG_CONTRACT.md`
- `docs/09_MASTERPLAN_STATUS.json`

## Anwendung
ZIP im Repository-Root entpacken und Dateien überschreiben.

## Validierung
```bash
cd SecondBrain-Agent
pytest -q tests/test_v3014_p1_embedding_config_contract.py tests/test_v3012_p1_provider_health_gate.py
python launcher.py p1-embedding-config --write-report
python launcher.py p1-provider-health --write-report
```

## Erwartung
- Ohne produktiven Provider: BLOCKED, kein falsches PASS.
- Mit `SECONDBRAIN_EMBEDDING_PROVIDER=ollama/openai`: Config wird zentral validiert.
- Aktivierter Fallback blockiert das Production Gate.
