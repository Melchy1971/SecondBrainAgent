# v30.15 P1 Embedding Dimension Contract

## Ziel

Produktive Embedding-Provider dürfen nicht mehr nur technisch erreichbar sein. Sie müssen auch zur konfigurierten Vektor-Dimension passen. Dadurch werden falsche pgvector-Indizes, Reindex-Drift und scheinbar grüne Provider-Health-Checks verhindert.

## Änderungen

- `provider_from_profile()` aktiviert Dimension-Enforcement für OpenAI und Ollama.
- OpenAI/Ollama Provider blockieren bei tatsächlicher Dimension != konfigurierter Dimension.
- Provider-Status enthält:
  - `configured_dimensions`
  - `dimension_contract_ok`
  - `enforce_dimensions`
- Provider Health blockiert mit `embedding_dimension_contract_failed`.
- Embedding-Konfiguration nutzt Provider-Defaults:
  - OpenAI: `1536`
  - Ollama/nomic: `768`
  - Local: `64`
- Neue Tests für Provider-Default-Dimensionen und Dimension-Mismatch.

## Akzeptanz

```bash
pytest -q tests/test_v3014_p1_embedding_config_contract.py tests/test_v3015_p1_embedding_dimension_contract.py tests/test_v3012_p1_provider_health_gate.py
pytest --collect-only -q
```

## Ergebnis

- Fokus-Suite: 15 PASS
- Collection: 1006 Tests gesammelt

## Konsequenz

P1-Production-Gate kann jetzt zwischen drei Fehlerklassen unterscheiden:

1. Provider nicht konfiguriert/erreichbar.
2. Provider nicht produktionsfähig wegen Fallback/Testdouble.
3. Provider erreichbar, aber Vektor-Dimension passt nicht zum Store-/Index-Vertrag.
