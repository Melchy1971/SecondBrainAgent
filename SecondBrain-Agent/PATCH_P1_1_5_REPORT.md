# PATCH P1.1.5 – Context Builder

## Ziel
RAG-Retrieval-Ergebnisse in einen promptfähigen, budgetierten Kontext überführen.

## Neue Dateien
- `secondbrain/rag/context_builder.py`
- `tests/test_p1_1_5_context_builder.py`

## Implementiert
- `ContextBuilderConfig`
- `ContextChunk`
- `BuiltContext`
- `ContextBuilder`
- stabile Sortierung nach Score, `document_id`, `chunk_id`
- Deduplizierung über normalisierten Text-Hash
- `max_chunks`-Limit
- `max_tokens`-Budget
- Oversized-Chunk-Truncation
- leere/blanke Resultate werden verworfen
- deterministische Token-Schätzung
- Source-Rendering mit Dokument-/Chunk-Referenz und optionalem Score

## Validierung
```text
python -m pytest tests/test_p1_1_5_context_builder.py -q
8 passed in 0.52s

python -m pytest -q
427 passed in 18.39s
```

## Risiko
Niedrig. Keine externen Abhängigkeiten. Keine Änderung bestehender APIs. Neues Modul ist additiv.
