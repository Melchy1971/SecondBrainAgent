# v30.63 – Background Agents

## Zweck

Jarvis führt wiederkehrende und langfristige Aufgaben eigenständig im Hintergrund aus: Monitore und periodische Wartung, registriert, geplant, mit Heartbeat, Supervisor und Failure-Policy.

## Wiederverwendete Bestandsobjekte

| Subsystem | Quelle | Rolle |
|-----------|--------|-------|
| Workflow Engine (v30.62) | `secondbrain/agent/workflow` (`WorkflowExecutor`) | jeder Agent-Run läuft als Workflow |
| Job Queue | `secondbrain/native/job_queue_center` (`JobQueueService`) | Runs werden als `agent`-Job gespiegelt (über die Workflow-Engine) |
| Notification Center | `secondbrain/native/notification_center` (`NotificationCenterService`) | Fehler-/Digest-/Health-Meldungen |
| Memory | injizierbarer `memory_sink` | Consolidation-Fakten |
| Runtime Health | Job-Queue-Snapshot (`snapshot()`) | Grundlage des System Health Agent |

Das bestehende `secondbrain/agent/background/` (In-Memory-Job-Manager) bleibt unangetastet – es ist ein anderes Konzept. Die neuen Background Agents liegen in `secondbrain/agent/background_agents/`.

## Neue Komponenten

| Klasse | Datei | Aufgabe |
|--------|-------|---------|
| `BackgroundAgent` | `models.py` | registrierter Agent (Typ, Schedule, Failure-Policy, Zustand) |
| `AgentSchedule` | `models.py` | Fälligkeit (Intervall; `<=0` = nur manuell) |
| `AgentRun` | `models.py` | ein Ausführungsdatensatz |
| `AgentHeartbeat` | `models.py` | Liveness (Sequence, Staleness) |
| `AgentFailurePolicy` | `models.py` | Verhalten bei wiederholten Fehlern |
| `AgentSupervisor` | `supervisor.py` | Registry, Lebenszyklus, Ausführung, Heartbeat, Failure-Policy |
| `BackgroundAgentStore` | `store.py` | Persistenz (agents/runs/heartbeats) |
| built-in handlers | `handlers.py` | die 6 Agent-Typen |

## Agent-Typen

| Typ | Prüft | Reuse |
|-----|-------|-------|
| `import_monitor` | Import-Jobs (blocked/failed) | Job Queue Snapshot |
| `knowledge_quality_monitor` | Quality-Score gegen Schwelle | konfigurierbarer Report |
| `memory_consolidation` | schreibt Consolidation-Marker | Memory Sink |
| `rag_index_monitor` | RAG-Index-Status vorhanden | konfigurierbare Statusdatei |
| `notification_agent` | sendet Digest-Meldung | Notification Center |
| `system_health_agent` | Queue-Health, meldet Degradation | Job Queue + Notification Center |

Handler geben bei erfolgreichem Lauf ein Ergebnis (inkl. Befunde) zurück; eine Ausnahme = Run-Fehler (Failure-Policy greift). Handler sind pro Agent überschreibbar.

## Funktionen

- **Agent registrieren** – `register(name, type, schedule, failure_policy, config)`.
- **Agent starten / stoppen / pausieren** – `start`/`stop`/`pause`/`resume` (Zustände REGISTERED/ACTIVE/PAUSED/STOPPED/FAILED).
- **Agent Status** – `status()` mit Agent, Heartbeat, Staleness, letztem Run, nächster Fälligkeit.
- **Heartbeat** – bei jeder Lifecycle-Aktion und um jeden Run (running → idle/failed); Sequence steigt monoton, Staleness über TTL.
- **Ausführung** – `run_agent()` läuft nur bei Zustand ACTIVE (sonst `skipped`), führt den Handler als 1-Schritt-Workflow aus.
- **Scheduling** – `run_due(now)` startet alle ACTIVE-Agenten, deren Intervall fällig ist.
- **Fehlerbehandlung** – Fehler zählt `consecutive_failures`; bei Erreichen von `max_consecutive_failures` greift die Aktion (`pause` → PAUSED, `stop` → FAILED, `alert_only` → ACTIVE) und es wird benachrichtigt. Erfolg setzt den Zähler zurück.

## Launcher-Kommandos

```
python launcher.py background-agent-register --name TEXT --type TYPE [--interval SEK] [--max-failures N] [--on-failure pause|stop|alert_only]
python launcher.py background-agent-list
python launcher.py background-agent-start   <agent_id>
python launcher.py background-agent-stop    <agent_id>
python launcher.py background-agent-pause   <agent_id>
python launcher.py background-agent-status  <agent_id>
python launcher.py background-agent-run     <agent_id> [--force]
python launcher.py background-agent-run-due
python launcher.py background-agent-runs    [<agent_id>] [--limit N]
```

## Tests

- `test_background_agents.py` – Registrierung, Lebenszyklus, alle 6 Typen, Memory-/Notification-/Health-Handler, Fehlerfälle.
- `test_agent_supervisor.py` – Failure-Policy (pause/stop/reset), Scheduling (`run_due`-Intervall), Ausführung über die Workflow-Engine + Job-Queue-Spiegelung.
- `test_agent_heartbeat.py` – Initial-Heartbeat, Sequence, running→idle/failed, Staleness, Status.

## Qualitätsnachweis

```
python -m compileall secondbrain/agent/background_agents launcher.py
pytest tests/test_background_agents.py tests/test_agent_supervisor.py tests/test_agent_heartbeat.py -q
```

Erwartung: 27 passed. Keine Regression in v30.62-Workflow, v30.61-Safety, Planner. Zielinterpreter Python 3.11+.

## Hinweis Scheduler

`AgentSchedule` ist intervallbasiert; `run_due` wird von außen getaktet (z. B. durch einen bestehenden Scheduler / scheduled task). Es wurde kein zweiter Ausführungs- oder Queue-Mechanismus eingeführt.
