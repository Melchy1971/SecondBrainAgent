# PATCH P0.5 — PDF Document Understanding Repair

## Ziel
PDF-Ingestion darf kein leerer Stub mehr sein. Der Dokumentenpfad muss echten Text extrahieren, Chunks erzeugen und suchbar machen.

## Änderungen

### secondbrain/document_understanding/runtime.py
- `.pdf` Routing von `_read_pdf_stub()` auf `_read_pdf()` umgestellt.
- Primärer PDF Reader: PyMuPDF (`fitz`).
- Fallback Reader: `pypdf`.
- Seitenmarker `[page n]` ergänzt, damit später zitierfähige Page-Locations möglich sind.
- Fehler-Metadaten strukturiert zurückgegeben.
- `_read_pdf_stub()` als Rückwärtskompatibilitäts-Alias erhalten.

### tests/test_document_understanding.py
- Test `test_ingest_file_pdf_extracts_text` ergänzt.
- Test erzeugt eine echte PDF-Datei, ingestiert sie, prüft Chunks und Suche.

## Validierung

```bash
pytest tests/test_document_understanding.py -q
# 6 passed in 0.78s

pytest -q
# 393 passed in 17.61s
```

## Ergebnis
P0-Dokumentenverständnis verbessert. PDF-Import ist jetzt funktional statt Stub.

## Bekannte Grenzen
- OCR für gescannte PDFs ist weiterhin nicht implementiert.
- Tabellenextraktion aus PDFs ist weiterhin nicht implementiert.
- Page-basierte Citation-Locations werden vorbereitet, aber noch nicht vollständig in die Citation-Tabelle verdrahtet.
