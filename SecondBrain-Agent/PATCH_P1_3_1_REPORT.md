# PATCH P1.3.1 – Document Parser Contract

## Ziel
Dokumentenverständnis/Ingestion stabilisieren durch einen expliziten Parser-Vertrag vor der bestehenden Ingestion-Runtime.

## Enthaltene Änderungen

### Neue Dateien
- `secondbrain/document_understanding/parser_contract.py`
- `secondbrain/document_understanding/parsers.py`
- `secondbrain/document_understanding/ingestion_contract.py`
- `tests/test_p1_3_1_document_parser_contract.py`

### Geänderte Datei
- `secondbrain/document_understanding/__init__.py`

## Funktionale Wirkung
- Einheitliches `ParsedDocument`-Modell für Parser-Ausgaben.
- Stabile Parse-Statuswerte: `parsed`, `empty`, `unsupported`, `failed`.
- Textnormalisierung mit Erhalt von Absatzgrenzen.
- Default Parser Registry für Text, Markdown, CSV, JSON, EML und PDF.
- Unsupported-Dateien erzeugen kontrollierten Status statt ungefangener Pipeline-Fehler.
- Adapter `ParsedDocumentIngestionService` übergibt nur valide Parse-Ergebnisse an die bestehende `ingest_text`-Boundary.
- Bestehender Export `DocumentUnderstandingRuntime` bleibt kompatibel.

## Validierung

```text
485 passed in 14.05s
```

## Risiko reduziert
- Parser-Library-Details leaken nicht mehr in Ingestion/RAG.
- Leere/kaputte/unsupported Dateien brechen keine Sync- oder Importpipeline.
- Nächster Ausbau OCR/Table Extraction kann hinter demselben Vertrag erfolgen.
