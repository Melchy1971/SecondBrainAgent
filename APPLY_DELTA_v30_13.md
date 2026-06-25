# Apply Delta v30.13 P1 Golden Quality Gate

## Ziel
Delta auf den aktuellen Stand v30.12 anwenden.

## Enthalten
- `SecondBrain-Agent/secondbrain/p1_golden_retrieval.py`
- `SecondBrain-Agent/secondbrain/p1_production_gate.py`
- `SecondBrain-Agent/config/golden_retrieval.json`
- `SecondBrain-Agent/tests/test_v3013_p1_golden_quality_gate.py`
- `SecondBrain-Agent/docs/releases/v30_13_P1_GOLDEN_QUALITY_GATE.md`
- `SecondBrain-Agent/docs/09_MASTERPLAN_STATUS.json`

## Anwendung
ZIP im Repository-Root entpacken, sodass `SecondBrain-Agent/...` überschrieben wird.

## Validierung
```bash
cd SecondBrain-Agent
pytest --collect-only -q
pytest -q tests/test_v3013_p1_golden_quality_gate.py tests/test_v3012_p1_provider_health_gate.py
python launcher.py p1-golden-eval
python launcher.py p1-production
```

## Erwartung
- Collection: 996 Tests.
- Fokus-Suite: 10 PASS.
- `p1-golden-eval` blockiert Qualitätsfehler mit `technical_ok=true` und `quality_ok=false`.
