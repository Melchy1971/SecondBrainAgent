# APPLY DELTA v30.56

## Delta und Incremental Import

- Verwendet ausschließlich die bestehende Enterprise Import Engine und Runtime-Queue.
- Stabile Dokumentidentitäten plus SHA-basierte Content-Hashes steuern Change Detection und Deduplication.
- Neue Dokumente werden angelegt, geänderte Dokumente aktualisiert, unveränderte und inhaltsgleiche Duplikate übersprungen.
- Jede neue/geänderte Fassung wird in `document_versions` innerhalb der bestehenden RAG-Datenbank versioniert.
- Abgebrochene Imports werden automatisch am Checkpoint fortgesetzt; transiente Importfehler und Pipeline-Jobs verwenden exponentielle Retries.
- Nur neue/geänderte Dokument-IDs durchlaufen Chunk, Embedding, Memory, Graph und Search.
- Bei aktiviertem PostgreSQL/pgvector werden Dokumente, Chunks und Vektoren per COPY-Staging und Upsert synchronisiert.

## Prüfung

```powershell
.\.venv\Scripts\python.exe -m compileall -q secondbrain modules tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe launcher.py repo-doctor --execute-runtime-checks
```
