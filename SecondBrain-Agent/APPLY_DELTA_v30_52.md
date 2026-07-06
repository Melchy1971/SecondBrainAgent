# APPLY DELTA v30.52

## Parallel Import Runtime

- Erweitert den vorhandenen `JobQueueService`; es wird keine zweite Queue oder Taskverwaltung angelegt.
- Pipeline: `chunk -> embedding -> memory -> graph -> search`.
- CPU-abhängiger, über `SECONDBRAIN_IMPORT_WORKERS` konfigurierbarer `WorkerPool`.
- Persistente Retries mit exponentiellem Backoff und Dead-Letter-Status in derselben Queue.
- Deduplizierte Stage-Jobs pro Import-Session und Batch.
- Der Streaming-Import wartet nicht auf Embeddings; die AI-Workspace-Runtime verarbeitet die Jobs parallel.

## Prüfung

```powershell
.\.venv\Scripts\python.exe -m compileall -q secondbrain modules tests
.\.venv\Scripts\python.exe -m pytest -q
```
