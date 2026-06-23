# PATCH P1.3.7 - Ingestion Index Bridge

## Ziel
Erfolgreiche Dokument-Ingestion wird deterministisch an die RAG-Reindexierung gekoppelt.

## Änderungen
- `secondbrain/document_understanding/index_bridge.py`
  - `IngestionIndexBridge`
  - `IngestionIndexDocument`
  - `IngestionIndexResult`
  - `InMemoryIngestionIndexSink`
  - Skip-Regeln für rejected/failed ingestion results
  - Failure-Isolation für Index- und Delete-Seiteneffekte
- `secondbrain/document_understanding/__init__.py`
  - neue Bridge-Exports
- `secondbrain/document_understanding/runtime.py`
  - Kompatibilität zwischen legacy SQLite Runtime und P1.3 Parser-Service wiederhergestellt
  - PDF-Text-Extraktion über PyMuPDF/pypdf als Runtime-Fallback
- `secondbrain/document_understanding/quality_gate.py`
  - Review-Schwelle präzisiert
  - `NO_PAGE_BOUNDARIES` nur noch für PDF relevant, nicht für Plain-Text-Dokumente
- `tests/test_p1_3_7_ingestion_index_bridge.py`
  - neue Bridge-Tests für Index, Skip, Reindex, Delete, Failure-Isolation

## Validierung
```text
519 passed in 19.05s
```

## Status
P1.3 Dokumentenverständnis ist jetzt durchgängig verdrahtet:
Parser -> Quality Gate -> Ingestion Pipeline -> RAG Reindex Plan.
