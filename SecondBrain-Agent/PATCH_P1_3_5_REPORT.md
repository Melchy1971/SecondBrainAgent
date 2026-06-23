# PATCH P1.3.5 - Ingestion Quality Gate

## Ziel
Parser-Ergebnisse werden vor Ingestion, Chunking und Indexierung deterministisch bewertet.

## Änderungen
- Neuer Qualitäts-Gate-Service:
  - `secondbrain/document_understanding/quality_gate.py`
- Export in:
  - `secondbrain/document_understanding/__init__.py`
- Tests:
  - `tests/test_p1_3_5_ingestion_quality_gate.py`

## Implementierte Fähigkeiten
- Accept/Reject/Review-Entscheidung
- Reject-Gründe:
  - Parser failed
  - Unsupported type
  - OCR required
  - Empty content
  - Below min chars
  - Below min words
  - Missing title
  - Missing MIME type
  - Source path mismatch
  - Disallowed MIME type
- Review-Gründe:
  - Very short content
  - No page boundaries
  - Parser warnings
  - No source path
- Policy-Objekt für Schwellenwerte und erlaubte MIME-Typen
- JSON-/Dict-fähiges Ergebnisobjekt für UI, Logs und Release-Gates

## Validierung
```text
python -m pytest -q tests/test_p1_3_5_ingestion_quality_gate.py
5 passed in 0.28s
```

## Risiko reduziert
- Keine stillen Imports leerer oder fehlerhafter Dokumente
- OCR-Pflicht wird explizit blockiert
- Unsupported-Dateien gelangen nicht in RAG
- Schwache Parser-Ergebnisse sind auditierbar
