# v30.11 P1 Vector Dimension Drift Guard

## Ziel
P1 Production Gate darf nicht bestehen, wenn Embeddings mit gleicher Provider-ID, aber anderer Vektordimension im Index liegen.

## Änderung
- `p1_vector_provider_guard` erkennt jetzt `dimension_mismatch_vectors`.
- Blocker wird ausgelöst, wenn gespeicherte Vektor-Dimensionen nicht zur aktuellen Provider-Dimension passen.
- Remediation verweist auf Reindex nach Provider-/Modell-/Dimensionswechsel.
- `p1_production_gate` zeigt Dimension Drift im Detail des Vector Provider Audits.

## Akzeptanz
```bash
pytest -q tests/test_v187_p1_vector_provider_guard.py -q
```

Ergebnis: `6 PASS`.

## Konsequenz
Modellwechsel mit gleicher Provider-ID erzeugt keinen falschen PASS mehr. Reindex ist erzwingbar und auditierbar.
