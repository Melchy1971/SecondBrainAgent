# Apply Delta v30.18 — P1 Vector Index Repair

## Inhalt

Dieses Delta ergänzt die deterministische Reparatur für Vektorindex-Drift nach Provider-, Modell- oder Dimensionswechseln.

## Anwenden

ZIP im Repository-Root entpacken, sodass der Ordner `SecondBrain-Agent/` überschrieben wird.

## Validieren

```bash
cd SecondBrain-Agent
pytest -q tests/test_v3017_p1_embedding_index_identity.py tests/test_v3018_p1_vector_index_repair.py
pytest --collect-only -q
python launcher.py p1-vector-provider-audit --write-report
python launcher.py p1-vector-index-repair --write-report
```

## Erwartung

- Fokus-Suite: 7 PASS
- Collection: 1016 Tests
- Volltest: außerhalb Sandbox-Timeout ausführen
