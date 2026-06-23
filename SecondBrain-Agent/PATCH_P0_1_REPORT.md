# SecondBrain-Agent Patch P0.1

## Ziel
Testsammlung und Basistestlauf wiederherstellen.

## Geänderte Dateien

- `secondbrain/rag.py`
  - Legacy-Modul als Package-kompatibel markiert.
  - `secondbrain.rag.<module>` funktioniert wieder trotz vorhandener Datei `rag.py` und Ordner `rag/`.

- `secondbrain/connectors.py`
  - Legacy-Modul als Package-kompatibel markiert.
  - `secondbrain.connectors.<module>` funktioniert wieder trotz vorhandener Datei `connectors.py` und Ordner `connectors/`.

- `secondbrain/ga/chaos_suite.py`
- `secondbrain/ga/deployment_manager.py`
- `secondbrain/ga/observability.py`
- `secondbrain/ga/performance_suite.py`
- `secondbrain/ga/release_gate.py`
- `secondbrain/ga/release_report.py`
- `tests/test_v270_ga_hardening.py`
  - Fehlerhafte Literal-Zeichen `\\n` am Dateiende entfernt.

- `secondbrain/rag/vector_search_service.py`
  - `hybrid_score` für reine Vector-Search-Ergebnisse auf Repository-Score gesetzt.
  - Verhindert künstliche Abwertung, wenn keine BM25-/Recency-/Importance-Signale vorhanden sind.

- `secondbrain/agent/workflow_executor.py`
  - Unbekannte Tools schlagen jetzt fehl.
  - Vorheriger Fehler: unbekannte Tools wurden als `SKIPPED` behandelt und Workflow endete fälschlich mit `COMPLETED`.

## Validierung

```bash
python -m pytest -q
```

Ergebnis:

```text
383 passed in 19.72s
```

## Nicht enthalten

Dieser Patch behebt nur P0.1/P0.2-Testbruch. Nicht enthalten:

- echte RAG-Produktionsreife
- echte Connector-Produktionsreife
- Packaging-Bereinigung
- Doku-Version-Source-of-Truth
- Full-Repo-Cleanup
