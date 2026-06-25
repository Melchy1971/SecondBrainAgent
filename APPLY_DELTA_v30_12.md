# Delta v30.12 anwenden

## Inhalt
- `SecondBrain-Agent/secondbrain/p1_provider_health.py`
- `SecondBrain-Agent/secondbrain/p1_production_gate.py`
- `SecondBrain-Agent/secondbrain/module_registry.py`
- `SecondBrain-Agent/launcher.py`
- `SecondBrain-Agent/tests/test_v3012_p1_provider_health_gate.py`
- `SecondBrain-Agent/config/golden_retrieval.json`
- `SecondBrain-Agent/docs/09_MASTERPLAN_STATUS.json`
- `SecondBrain-Agent/docs/releases/v30_12_P1_PROVIDER_HEALTH_GATE.md`

## Manuell löschen
- `SecondBrain-Agent/config/olden_retrieval.json` falls vorhanden. Tippfehler-Datei wird durch `golden_retrieval.json` ersetzt.

## Validierung
```bash
cd SecondBrain-Agent
PYTHONPATH=. pytest -q tests/test_v3012_p1_provider_health_gate.py tests/test_v186_p1_production_golden_gate.py tests/test_v185_p1_golden_retrieval.py
PYTHONPATH=. pytest --collect-only -q
python launcher.py p1-provider-health --write-report
python launcher.py p1-production --write-report
```

## Erwartung
- Fokus-Suite: 14 PASS
- Collection: 991 Tests
- `p1-provider-health` blockiert lokale deterministische Embeddings für Production Readiness.
- `p1-production` enthält `embedding_provider_production_ready` als harten Blocker.
