# PATCH P0.2 - Package Repair / Minimal Production Hardening

## Ziel
Stabilisierung der zuvor nur notdürftig reparierten Package-Konflikte `secondbrain.rag` und `secondbrain.connectors`.

## Änderungen

### RAG
- `secondbrain/rag/__init__.py` ergänzt.
- Legacy-Funktionen aus `secondbrain/rag.py` als Package-Exports bereitgestellt:
  - `chunk_text`
  - `build_rag_index`
  - `search_rag`
  - `write_rag_answer`
- `HybridScoreCalculator` gehärtet:
  - Weight-Normalisierung
  - Reject negativer/ungültiger Gewichte
  - Score-Clamping auf 0..1
  - `score_mapping()` ergänzt
- `VectorSearchService` gehärtet:
  - Repository-Vertrag geprüft
  - `limit <= 0` liefert leere Liste
  - Zusatzsignale aus Metadata: BM25, Recency, Importance
  - Sortierung nach Hybrid Score
  - Legacy-Verhalten bleibt erhalten: ohne Zusatzsignale ist `hybrid_score == semantic_score`

### Connectors
- `secondbrain/connectors/__init__.py` ergänzt.
- `IncrementalSyncEngine` erweitert:
  - Legacy-Listen-Diff bleibt kompatibel
  - Mapping-Diff mit Revisionserkennung ergänzt
  - Ergebnisfelder: `added`, `removed`, `updated`, `unchanged`
  - `has_changes()` ergänzt

### Tests
- `tests/test_p0_2_package_repair.py` ergänzt.
- Abgedeckt:
  - Incremental Sync List Legacy Contract
  - Incremental Sync Mapping-Diff
  - Hybrid Score Grenzen/Gewichte
  - Fehlerfall invalid weights
  - Vector Search Sortierung nach Hybrid Score

## Validierung

```bash
pytest -q
```

Ergebnis:

```text
388 passed in 19.49s
```

## Risiko / Folgearbeiten

- `secondbrain/rag.py` und `secondbrain/connectors.py` existieren weiter als Legacy-Dateien. Die Package-Initialisierung macht die Imports stabil, aber die Altdateien sollten später konsolidiert oder entfernt werden.
- RAG ist weiterhin nur teilproduktiv: echte Embedding-/Index-/Persistenzqualität ist P1.
- Connector-Framework besitzt jetzt stabile Diff-Logik, aber echte API-Syncs sind P1/P4.
