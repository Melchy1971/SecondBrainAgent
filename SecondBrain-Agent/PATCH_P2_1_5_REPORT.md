# PATCH P2.1.5 — Desktop Background Jobs

## Inhalt

- `secondbrain.desktop.jobs.job_state`
- `secondbrain.desktop.jobs.job_registry`
- `secondbrain.desktop.jobs.job_runner`
- `secondbrain.desktop.jobs.job_history`
- `secondbrain.desktop.jobs.background_executor`
- `secondbrain.desktop.jobs.job_manager`

## Wirkung

- Zentrale Job-Verwaltung für Desktop-Shell
- Job-Lifecycle: created, queued, running, completed, failed, cancelled, timeout
- Handler-Registry für Import, Reindex, Connector Sync, OCR, Diagnostics, Backup, Upgrade
- Event-Auslösung für Job-Statusänderungen
- Persistenter Job-Verlauf als JSON
- Background-Ausführung via ThreadPoolExecutor

## Validierung

`12 passed in 0.34s`

## Grenzen

- Kein harter Thread-Abbruch für bereits laufende Jobs
- Keine echte GUI-Thread-Marshalling-Schicht
- Keine Datenbank-Persistenz, bewusst JSON-basiert für Desktop Foundation
