# v30.12 P1 Provider Health Gate

## Ziel
Production Gate darf keinen impliziten Produktivstatus erzeugen, wenn nur lokale deterministische Embeddings oder explizite Fallbacks aktiv sind.

## Änderungen
- Neuer Check `secondbrain.p1_provider_health.v1`.
- Neuer Launcher-Befehl `p1-provider-health`.
- `p1-production` enthält neuen Blocker `embedding_provider_production_ready`.
- Lokale deterministische Embeddings bleiben für Tests zulässig, werden aber für Production Readiness blockiert.
- `config/golden_retrieval.json` als korrekter Golden-Dataset-Pfad ergänzt.

## Validierung
```bash
PYTHONPATH=. pytest -q tests/test_v3012_p1_provider_health_gate.py tests/test_v186_p1_production_golden_gate.py tests/test_v185_p1_golden_retrieval.py
PYTHONPATH=. pytest --collect-only -q
```

Ergebnis:
- 14 PASS
- 991 Tests gesammelt

## Weiter offen
- Vollständiger `pytest -q` ohne Sandbox-Timeout.
- Live-Test gegen echte pgvector-VPS-DB.
- Echtprovider-Health-Probe für OpenAI/Ollama in Zielumgebung.
