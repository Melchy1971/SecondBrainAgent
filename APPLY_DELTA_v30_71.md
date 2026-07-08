# Delta v30.71 anwenden – Scheduler (Recurring Jobs / Cron / Dependencies / Maintenance)

## 1. Dateien übernehmen

Inhalt aus `SecondBrain-Agent/` in dein Projektverzeichnis `SecondBrain-Agent/` kopieren, bestehende Dateien überschreiben.

Neu:

- `secondbrain/agent/scheduler/__init__.py`
- `secondbrain/agent/scheduler/cron.py`
- `secondbrain/agent/scheduler/models.py`
- `secondbrain/agent/scheduler/store.py`
- `secondbrain/agent/scheduler/scheduler.py`
- `secondbrain/agent/scheduler/maintenance.py`
- `tests/test_cron.py`
- `tests/test_scheduler.py`
- `tests/test_dependencies.py`
- `tests/test_maintenance.py`
- `docs/releases/v30_71_scheduler.md`

Geändert: `README_PATCH.md`, `RELEASE_NOTES.md`.

Kein Launcher-/GUI-Eingriff (Library-Ebene).

## 2. Qualität prüfen

```powershell
python -m compileall .
pytest -q
```

Gezielt:

```powershell
pytest tests/test_cron.py tests/test_scheduler.py tests/test_dependencies.py tests/test_maintenance.py -q
```

Erwartung: 25 passed. Zielinterpreter Python 3.11+.

## 3. Nutzung

```python
from secondbrain.agent.scheduler import JobScheduler

sch = JobScheduler(project_root, memory_sink=my_sink)
sch.register_maintenance()                                  # health/auto_index/knowledge_refresh/memory_consolidation
sch.add("report", "0 8 * * 1-5", kind="system")             # Cron: Werktags 08:00
sch.add("sync", {"interval_seconds": 900})                  # alle 15 Minuten

# von aussen getaktet (z.B. minuetlich):
runs = sch.run_due()                                        # enqueued in die Job Queue + fuehrt Handler aus
```

## 4. Hinweise

- Keine zweite Queue: jede Auslösung wird über `JobQueueService.add_job` in die bestehende Job Queue gespiegelt.
- `run_due` braucht einen externen Takt (bestehender Scheduler / scheduled task / Loop); kein eigener Daemon.
- Dependency Scheduler: abhängige Jobs laufen erst nach erfolgreichem Vorlauf; sonst `skipped`.
- Cron: 5 Felder (`min hour dom month dow`), unterstützt `*`, `*/n`, `a-b`, `a,b`.
