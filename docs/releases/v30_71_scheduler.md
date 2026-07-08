# v30.71 – Scheduler (Recurring Jobs / Cron / Dependencies / Maintenance)

## Zweck

Wiederkehrende und geplante Jobs mit Cron-Ausdrücken, Abhängigkeiten und eingebauter Wartung. Jede Auslösung wird in die bestehende native Job Queue gespiegelt – keine zweite Queue.

## Wiederverwendung

`JobScheduler` enqueued jede fällige Auslösung über `JobQueueService.add_job(kind, name, payload)` (v30.44). Der Health-Check liest `JobQueueService.snapshot()`. Memory Consolidation nutzt einen injizierbaren `memory_sink`.

## Komponenten

Modul: `secondbrain/agent/scheduler/`

| Klasse/Datei | Aufgabe |
|--------------|---------|
| `CronSchedule` / `IntervalSchedule` (`cron.py`) | 5-Feld-Cron (`*`, `*/n`, `a-b`, `a,b`) + Intervall; `matches`, `due`, `next_after` |
| `RecurringJob` / `JobRun` (`models.py`) | Job-Definition + Lauf-Datensatz |
| `SchedulerStore` (`store.py`) | Persistenz (recurring_jobs.json, runs.jsonl) |
| `JobScheduler` (`scheduler.py`) | Registrierung, Fälligkeit, Dependency-Zyklus, Job-Queue-Spiegelung |
| `maintenance.py` | eingebaute Wartungsjobs + Handler |

## Funktionen

- **Recurring Jobs / Cron:** `add(name, "*/15 * * * *")` oder `{"interval_seconds": n}`. `due` prüft, ob seit dem letzten Lauf eine Auslösung fiel (1-Tag-Fenster), bounded.
- **Dependency Scheduler:** ein Job mit `dependencies=[...]` läuft erst, wenn seine Voraussetzungen im selben Zyklus erfolgreich waren (oder zuvor `last_status == success`). Fällt eine Voraussetzung aus, wird der abhängige Job `skipped` (`dependency_not_satisfied:<id>`). Reihenfolge per topologischer Sortierung.
- **Maintenance / Health Checks / Knowledge Refresh / Auto Index / Memory Consolidation:** `register_maintenance()` registriert vier Jobs:
  - `health_check` – `*/15 * * * *`, liest den Queue-Snapshot.
  - `auto_index` – `0 * * * *` (stündlich).
  - `knowledge_refresh` – `0 3 * * *`, **abhängig** von `auto_index`.
  - `memory_consolidation` – `0 4 * * *`, liefert an den `memory_sink`.

## Run-Zyklus

`run_due(now)` ermittelt fällige Jobs, sortiert nach Abhängigkeiten, enqueued je Job einen Queue-Job (Reuse) und führt den Handler aus. Ergebnis: Liste von `JobRun` (success/failed/skipped); `last_run_at`, `last_status`, `run_count` werden persistiert.

## Tests

- `test_cron.py` – Parsing, `matches` (`*/15`, Stunden, Ranges/Listen, Wochentage), `due`-Fenster, `next_after`, Intervall.
- `test_scheduler.py` – Registrierung, Intervall-Fälligkeit, Queue-Spiegelung, Deaktivierung, Lauf-Historie, Cron-Treffer.
- `test_dependencies.py` – Reihenfolge, Skip bei Fehlschlag der Voraussetzung, unbekannte Abhängigkeit, nicht-fällige Voraussetzung mit Vorerfolg.
- `test_maintenance.py` – vier Wartungsjobs, Health-Snapshot, Memory-Sink, `knowledge_refresh` nach `auto_index`, Queue-Spiegelung.

## Qualitätsnachweis

```
python -m compileall secondbrain/agent/scheduler
pytest tests/test_cron.py tests/test_scheduler.py tests/test_dependencies.py tests/test_maintenance.py -q
```

Erwartung: 25 passed. Keine Regression in v30.61–v30.70. Zielinterpreter Python 3.11+.

## Hinweis

`run_due` wird von außen getaktet (z. B. minütlich durch einen bestehenden Scheduler/scheduled task oder einen Loop). Der Scheduler selbst ist deterministisch und ohne eigenen Daemon – so bleibt er testbar und ohne Parallel-Runtime.
