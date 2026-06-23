# PATCH P1.3.3 — PDF/OCR Parser Facade

## Ziel
PDF-Ingestion darf gescannte oder bildbasierte PDFs nicht als leere Dokumente importieren. Der Parser liefert jetzt deterministische Statuswerte für Text-PDFs, OCR-pflichtige PDFs, nicht unterstützte Dateien und harte Parserfehler.

## Änderungen

### Geändert
- `secondbrain/document_understanding/parser_contract.py`
  - `ParseStatus.OCR_REQUIRED` ergänzt.
- `secondbrain/document_understanding/parsers.py`
  - `PdfTextParser` markiert PDFs ohne extrahierten Text als `ocr_required` statt als `empty`.
  - PyMuPDF-/pypdf-Ergebnisse werden nach `char_count` bewertet.
- `secondbrain/document_understanding/ingestion_contract.py`
  - `ocr_required` blockiert Ingestion wie `failed`, `empty`, `unsupported`.
- `secondbrain/document_understanding/__init__.py`
  - `PdfOcrParserFacade` exportiert.

### Neu
- `secondbrain/document_understanding/pdf_facade.py`
  - `PdfOcrParserFacade`
  - Textparser-first-Strategie
  - optionaler OCR-Parser
  - deterministische Fallbacks:
    - `parsed`
    - `ocr_required`
    - `failed`
- `tests/test_p1_3_3_pdf_ocr_facade.py`
  - Text-PDF ohne OCR
  - Scan-PDF ohne OCR-Parser
  - Scan-PDF mit OCR-Parser
  - defekter PDF-Textparser bleibt `failed`

## Validierung
```text
18 passed in 0.43s
```

## Risiko reduziert
- Keine stillen Leerimporte gescannter PDFs.
- Keine falsche Erfolgsmeldung bei OCR-Bedarf.
- OCR kann später als austauschbarer Adapter ergänzt werden.
