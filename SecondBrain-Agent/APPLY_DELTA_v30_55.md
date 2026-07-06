# APPLY DELTA v30.55

## Native Import Center

- Erweitert den vorhandenen AI Workspace; keine zweite GUI.
- Anzeige für Datei, ETA, Fortschritt, Chats, Dokumente, Chunks, Embeddings, Worker, CPU und RAM.
- Steuerung über Pause, Continue, Retry und Stop auf bestehenden Session-/Queue-Zuständen.
- Logs und Fehler stammen aus `job_history.jsonl` und `import_sessions`.
- Launcher: `import-center`, `import-status`, `import-history`.

## Prüfung

```powershell
.\.venv\Scripts\python.exe -m compileall -q secondbrain modules tests
.\.venv\Scripts\python.exe -m pytest -q
```
