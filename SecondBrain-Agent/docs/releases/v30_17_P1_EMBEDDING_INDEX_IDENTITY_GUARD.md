# v30.17 P1 Embedding Index Identity Guard

## Ziel

Verhindern, dass Vektoren unterschiedlicher Embedding-Modelle unter demselben Provider-Label vermischt werden.

## Änderung

- `embedding_index_provider()` erzeugt stabile Index-Keys im Format `provider:model:dimensions`.
- Provider-Status enthält `index_provider`.
- RAG-Ingest und Reindex speichern Vektoren unter dem Index-Key statt nur unter `openai`, `ollama` oder `local-deterministic`.
- Vector Search filtert auf den aktuellen Index-Key.
- Provider Health meldet fehlenden Index-Key als Blocker.

## Wirkung

Ein Modellwechsel bei gleichem Provider erzeugt keinen still gemischten Index mehr. Bestehende Vektoren bleiben vorhanden, werden aber nicht mehr für Suchen mit neuer Provider-/Modell-/Dimensionsidentität verwendet. Reindex ist damit explizit notwendig.

## Validierung

```bash
pytest -q tests/test_v3017_p1_embedding_index_identity.py
pytest --collect-only -q
```

Ergebnis in Sandbox:

- Fokus-Suite: 4 PASS
- Collection: 1013 Tests gesammelt
