# Delta v30.63 anwenden – Background Agents

## 1. Dateien übernehmen

Inhalt aus `SecondBrain-Agent/` in dein Projektverzeichnis `SecondBrain-Agent/` kopieren, bestehende Dateien überschreiben.

Neu:

- `secondbrain/agent/background_agents/__init__.py`
- `secondbrain/agent/background_agents/models.py`
- `secondbrain/agent/background_agents/store.py`
- `secondbrain/agent/background_agents/handlers.py`
- `secondbrain/agent/background_agents/supervisor.py`
- `secondbrain/agent/background_agents/service.py`
- `secondbrain/agent/background_agents/cli.py`
- `tests/_bg_fakes.py`
- `tests/test_background_agents.py`
- `tests/test_agent_supervisor.py`
- `tests/test_agent_heartbeat.py`
- `docs/releases/v30_63_background_agents.md`

Geändert:

- `launcher.py` (Dispatch `background-agent-*`)
- `README_PATCH.md`, `RELEASE_NOTES.md`

## 2. Qualität prüfen

```powershell
python -m compileall .
pytest -q
```

Gezielt:

```powershell
pytest tests/test_background_agents.py tests/test_agent_supervisor.py tests/test_agent_heartbeat.py -q
```

Erwartung: 27 passed. Zielinterpreter Python 3.11+.

## 3. Funktion prüfen

```powershell
python launcher.py background-agent-register --name "Import Waechter" --type import_monitor --interval 3600
python launcher.py background-agent-start <agent_id>
python launcher.py background-agent-run <agent_id>
python launcher.py background-agent-status <agent_id>
python launcher.py background-agent-list
```

## 4. Hinweise

- Kein zweiter Ausführungsmechanismus: jeder Agent-Run läuft über die v30.62-Workflow-Engine und wird dadurch in der bestehenden Job Queue (`runtime/native/job_queue/`) gespiegelt.
- Persistenz unter `runtime/agent/background_agents/` (agents.json, runs.jsonl, heartbeats.json, atomar geschrieben).
- `run_due` wird von außen getaktet (bestehender Scheduler / scheduled task); `AgentSchedule.interval_seconds <= 0` = nur manuell.
- Failure-Policy-Aktionen: `pause` → PAUSED, `stop` → FAILED, `alert_only` → bleibt ACTIVE; jeweils mit Benachrichtigung.
