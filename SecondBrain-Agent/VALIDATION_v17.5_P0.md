# VALIDATION v17.5 P0

## Befehle

```bash
python launcher.py --project-root . p0-gate
python launcher.py --project-root . p0-smoke --write-report
PYTHONPATH=. python -m pytest -q
```

## Ergebnis

| Check | Ergebnis |
|---|---:|
| p0-gate | PASS |
| p0-smoke | PASS |
| pytest | 240 passed |

## Restrisiko

P0 prüft weiterhin nur lokale Start-, Import-, Config-, EventBus- und Runtime-Fitness. Externe Connectoren, OAuth, echte LLM-Aufrufe, PostgreSQL/pgvector und GUI-Interaktion bleiben außerhalb dieses Gates.
