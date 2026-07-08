# v30.62 – Agent Workflow Engine

## Zweck

Mehrstufige Agent-Pläne ausführbar machen: klassifiziert, freigabefähig, nach jedem Schritt gesichert und damit nach Approval **und** nach Absturz fortsetzbar.

## Wiederverwendete Bestandsobjekte

| Subsystem | Quelle | Rolle im Workflow |
|-----------|--------|-------------------|
| Agent Planner (Step-Schema) | `secondbrain/agent/workflow_models.py` (`WorkflowStep`, `WorkflowStatus`) | Schrittdefinition – nicht neu definiert |
| Tool Registry | `secondbrain/agent/tool_registry.py` (`ToolRegistry.run`) | Ausführung je Schritt |
| Approval Layer (v30.61) | `secondbrain/agent/safety` + `NativeApprovalQueue` | Freigabe für `requires_approval`-Schritte – **keine zweite Queue** |
| Job Queue | `secondbrain/native/job_queue_center` (`JobQueueService`) | Workflow als `agent`-Job gespiegelt |
| Notification Center | `secondbrain/native/notification_center` (`NotificationCenterService`) | Freigabe-/Fehler-/Abschluss-Meldungen |
| Recovery-Klassifikation | `secondbrain/agent/workflow_recovery.py` | Basis für Retry/Wait-Entscheidung |
| Memory | injizierbarer Sink (`memory_sink`) | erhält Schritt-/Ergebnis-Fakten |

Die bestehenden Stubs (`workflow_executor.py`, `dag_builder.py`) und `test_v303_agent_workflow_engine.py` bleiben unverändert lauffähig.

## Neue Komponenten

Modul: `secondbrain/agent/workflow/`

| Klasse | Datei | Aufgabe |
|--------|-------|---------|
| `Workflow` | `models.py` | Ausführbarer Mehrschritt-Plan |
| `WorkflowStep` | (re-export) | Schrittdefinition |
| `WorkflowState` | `models.py` | Lebenszyklus-Zustand |
| `WorkflowCheckpoint`, `StepRun` | `models.py` | Persistierter Lauf-Snapshot |
| `WorkflowStore` | `store.py` | Atomare JSON-Persistenz je Workflow |
| `WorkflowExecutor` | `executor.py` | Engine |
| `WorkflowRecovery` | `recovery.py` | Fehler → Strategie (Retry/Wait/Rollback/Fail) |
| `WorkflowAudit` | `audit.py` | Ereignis-Trail (JSONL) |
| `WorkflowService` | `service.py` | CLI-/Anwendungsfassade |

## Funktionen

- **Workflow starten** – `create()` erzeugt Checkpoint (Zustand `PENDING`), topologisch sortiert, Job in die Queue.
- **Schritt ausführen** – `run()` arbeitet Schritte in Abhängigkeitsreihenfolge ab.
- **Status speichern** – nach jedem Schritt wird der Checkpoint atomar geschrieben (`runtime/agent/workflows/<id>.json`).
- **Fehler behandeln** – Ausnahme je Schritt wird durch `WorkflowRecovery` klassifiziert.
- **Retry** – transiente Fehler werden bis `max_retries` wiederholt (TimeoutError auch typbasiert).
- **Rollback vorbereiten** – `prepare_rollback()` erzeugt den Reverse-Plan der abgeschlossenen Schritte; Zustand `ROLLBACK_READY`. Es wird **nicht** ausgeführt.
- **Nach Approval fortsetzen** – `resume()`/`resume_after_approval()` prüft die Freigabe in der native Queue und läuft weiter.
- **Nach Absturz fortsetzen** – `resume_after_crash()` setzt einen als `running` hinterlassenen Schritt zurück und läuft ab dem letzten Checkpoint weiter; abgeschlossene Schritte werden nicht wiederholt.

## Zustände

`PENDING → RUNNING → (WAITING_APPROVAL) → COMPLETED`
Fehlerpfade: `RETRYING`, `ROLLBACK_READY`, `FAILED`, `CANCELLED`.

## Launcher-Kommandos

```
python launcher.py workflow-create --objective TEXT (--steps-json JSON | --spec PATH)
python launcher.py workflow-run     <workflow_id>
python launcher.py workflow-status  <workflow_id>
python launcher.py workflow-list
python launcher.py workflow-cancel  <workflow_id>
python launcher.py workflow-resume  <workflow_id>
python launcher.py workflow-audit   [<workflow_id>] [--limit N]
python launcher.py workflow-rollback <workflow_id>
```

Step-Spec (JSON): `id`, `name`, `tool_name`, `input`, `dependencies`, `timeout_seconds`, `max_retries`, `requires_approval`.

## Tests

- `test_workflow_engine.py` – Mehrschritt-Ausführung, topologische Ordnung, No-op-Schritt, Rollback-Vorbereitung, List/Audit.
- `test_workflow_checkpoint.py` – Persistenz, Crash-Resume ab Checkpoint, Idempotenz, keine `.tmp`-Reste.
- `test_workflow_recovery.py` – Klassifikation, Retry-Budget, Approval-Wait, Retry-dann-Erfolg.
- `test_workflow_approval.py` – Halt am Approval-Schritt, Wiederverwendung der native Queue (identischer Pfad), Fortsetzen nach Approve, Fail nach Reject, keine Duplikate.

## Qualitätsnachweis

```
python -m compileall secondbrain/agent/workflow launcher.py
pytest tests/test_workflow_engine.py tests/test_workflow_checkpoint.py tests/test_workflow_recovery.py tests/test_workflow_approval.py -q
```

Erwartung: 21 passed. Keine Regression in `test_v303_agent_workflow_engine.py`, v30.61-Safety-Tests, Planner. Zielinterpreter Python 3.11+.

## Hinweis Memory

Der durable Ereignisspeicher des Workflows ist der `WorkflowAudit`-Trail. Die eigentliche SecondBrain-Memory wird über den optionalen `memory_sink` angebunden (Callable), da das Repo keine einheitliche schlanke Append-API der Memory bereitstellt. Ohne Sink bleibt der Audit-Trail die Quelle für Recovery und Nachschau.
