# APPLY DELTA v30.57

## Import Quality Scoring

- Nutzt ausschließlich die bestehende Import-Engine, RAG-Datenbank und Pipeline.
- Bewertet Duplicate/Near-Duplicate, Sprache, PII, Secrets, Klassifikation, Chunks, Embeddings, OCR, Parser und Source Trust.
- Jedes gechunkte Dokument erhält `knowledge_quality_score` von 0 bis 100 sowie einen Confidence Score.
- Bewertungen, Warnungen und Near-Duplicate-Signaturen liegen ausschließlich in `documents.metadata_json`.
- Exakte übersprungene Duplikate werden aus `import_delta_entries` projiziert.
- Quality Dashboard, Import Warnings und Duplicate Viewer sind Bereiche des vorhandenen Native Import Centers.

## Prüfung

```powershell
.\.venv\Scripts\python.exe -m compileall -q secondbrain modules tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe launcher.py repo-doctor --execute-runtime-checks
```
