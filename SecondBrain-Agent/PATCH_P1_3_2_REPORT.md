# PATCH P1.3.2 – Concrete Document Parsers

## Ziel
P1.3.1 Parser-Vertrag mit konkreten, robusten Parsern für Text, Markdown, JSON, JSONL, CSV und E-Mail erweitern.

## Enthaltene Änderungen

### Neue Datei
- `secondbrain/document_understanding/runtime.py`
- `tests/test_p1_3_2_concrete_document_parsers.py`

### Geänderte Dateien
- `secondbrain/document_understanding/__init__.py`
- `secondbrain/document_understanding/parsers.py`

## Funktionale Wirkung
- Markdown-Parser entfernt einfache YAML-Frontmatter.
- JSON-Parser erzeugt deterministisch sortierten Suchtext.
- JSONL-Parser zählt Records und normalisiert Zeilenobjekte.
- CSV-Parser erzeugt normalisierten, stabil chunkbaren Zeilentext.
- EML-Parser extrahiert zentrale Header und Plain-Text-Body.
- Missing File / Invalid JSON / Invalid CSV werden als ParseStatus.FAILED zurückgegeben statt Exceptions in die Pipeline zu werfen.
- `DocumentUnderstandingRuntime` stellt eine kompatible Runtime-Fassade bereit.

## Validierung

```text
14 passed in 0.06s
```

## Risiko reduziert
- Connector-Importe mit heterogenen Dateitypen können vor RAG-Indexierung deterministisch normalisiert werden.
- Fehlerhafte Dateien blockieren keine Batch-Ingestion.
- Parser-Ausgaben werden für Suche, Chunking und Audit konsistenter.
