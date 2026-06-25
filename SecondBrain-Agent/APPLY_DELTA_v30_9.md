# SecondBrainAgent Delta v30.9 — P1 Store-backed Vector Provider Audit

## Inhalt

Dieses Delta setzt den nächsten P1-Härtungsschritt um:

- `p1_vector_provider_guard` nutzt jetzt `runtime.rag_store.validation_snapshot()`.
- SQLite-only Annahme im Provider-Audit entfernt.
- pgvector/Store-Brücke kann Providerwechsel, fehlende Vektoren und Orphans prüfen.
- Legacy-SQLite-Fallback bleibt für ältere Runtimes erhalten.
- Neue Tests für store-backed Audit und Report-Schema.
- Masterplan-Status auf v30.9 aktualisiert.

## Anwenden

ZIP im Repository-Root entpacken und Dateien überschreiben.

## Validierung

```bash
cd SecondBrain-Agent
python -m pytest tests/test_v187_p1_vector_provider_guard.py tests/test_v309_p1_store_backed_vector_audit.py -q
python launcher.py p1-vector-provider-audit --write-report
```

## Erwartung

- Audit-Schema: `secondbrain.p1_vector_provider_guard.v1`
- Bei SQLite: `store_backend=sqlite`
- Bei pgvector: Audit läuft über den aktiven RagStore-Snapshot statt über `rag.sqlite3`
