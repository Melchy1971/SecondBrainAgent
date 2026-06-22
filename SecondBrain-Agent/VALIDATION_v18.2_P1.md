# Validation v18.2 P1

## Commands

```bash
python launcher.py p1-rag-ingest-text "Jarvis RAG Qualität Quellenprüfung Evidenz" --source unit --title V182
python launcher.py p1-rag-validate --write-report
python launcher.py p1-rag-quality "RAG Qualität" --write-report
python launcher.py p1-gate --write-report
PYTHONPATH=. pytest -q
```

## Ergebnis

| Check | Ergebnis |
|---|---:|
| p1-rag-validate | PASS |
| p1-rag-quality | PASS |
| p1-gate | PASS |
| pytest | 261 passed |

## Gate Schema

`secondbrain.p1_gate.v3`

## Risikoabbau

- Reduziert Halluzinationsrisiko durch explizite No-Evidence-Policy.
- Reduziert Index-Korruption durch Validierung von Chunks, Quellen, Token-Metadaten und Orphans.
- Erhöht CI-Fähigkeit durch maschinenlesbare Reports.
