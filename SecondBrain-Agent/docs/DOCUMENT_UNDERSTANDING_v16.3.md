# SecondBrain OS v16.3 – Document Understanding

## Ziel
v16.3 ergänzt Dokumentenverständnis als Grundlage für zitierfähiges RAG.

## Unterstützt
- TXT
- Markdown
- EML/Text
- DOCX XML-Reader
- XLSX Manifest-/Tabellen-Scaffold
- PPTX Textfragment-Reader
- PDF Stub für später PyMuPDF/pypdf

## Enthalten
- Dokument-Ingestion
- Chunking
- Citation Records
- Entity Extraction
- Tabellen-Scaffold
- SQLite Persistence
- RAG Answer Stub

## Befehle
```powershell
python launcher.py doc16-migrate
python launcher.py doc16-status
python launcher.py doc16-ingest-text "Jarvis Plan" "Jarvis nutzt Gmail und GitHub."
python launcher.py doc16-ingest-file .\sample_docs\demo.md
python launcher.py doc16-documents
python launcher.py doc16-search Gmail
python launcher.py doc16-entities
python launcher.py doc16-citations
python launcher.py doc16-answer "Was nutzt Jarvis?"
```

## Grenzen
- PDF-Extraktion ist Stub.
- OCR ist noch nicht integriert.
- LLM-Antwortgenerierung ist noch Stub.
- Tabellenextraktion ist vorbereitet, nicht vollständig.
