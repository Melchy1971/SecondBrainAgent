# APPLY DELTA v30.54

## Einheitlicher Dokumentimport

- Der bestehende `StreamingImportService` ist als zentraler `ImportService` auch für Dokumente zuständig.
- Vorhandene Parser werden für PST, EML, PDF, DOCX, XLSX, CSV, TXT und Markdown verwendet.
- Obsidian-, Notion-, Paperless- und OneNote-Exporte laufen als Quellenprofile durch denselben Service.
- Kanonische Dokument-Metadaten enthalten Parserstatus, Anhänge, OCR-Status, Version und Workspace.
- Document Explorer und ältere Document-Connector-Fassaden delegieren an denselben ImportService.
- Keine zweite Parser-Registry oder Dokumentdatenhaltung wurde eingeführt.

## Prüfung

```powershell
.\.venv\Scripts\python.exe -m compileall -q secondbrain modules tests
.\.venv\Scripts\python.exe -m pytest -q
```
