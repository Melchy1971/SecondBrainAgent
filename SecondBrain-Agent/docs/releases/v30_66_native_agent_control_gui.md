# v30.66 – Native Agent Control GUI

## Zweck

Alle Agent-Funktionen (v30.59–v30.65) in die bestehende native Desktop-Anwendung integrieren – als **eine** Agent-Control-Oberfläche im AI Workspace. Keine zweite GUI, keine zweite Navigation.

## Integration in den AI Workspace

- Neues Modul `secondbrain/native/agent_control/` (Aggregations-Service + GUI-Panel + CLI).
- In `secondbrain/native/ai_workspace/service.py` als Modul `agent_control` registriert (Navigation, Snapshot, `module_payload`). Die bestehenden Module bleiben unverändert.

## GUI-Bereiche

`AgentControlService` liefert acht Bereiche, jeder aus dem jeweiligen Bestands-Subsystem – ohne Neubau:

| Bereich | Quelle |
|---------|--------|
| Agenten | Zusammenfassung (Pläne, Workflows, Background Agents) |
| Pläne | `AgentPlanService` |
| Workflows | `WorkflowStore` (v30.62) |
| Background Agents | `AgentSupervisor` (v30.63) |
| Approvals | `SafetyService` / `NativeApprovalQueue` (v30.61) |
| Goals | `GoalTracker` (v30.65) |
| Audit | Safety-, Workflow-, Memory-Injection-Audit-Trails |
| Logs | `runtime/native/agent_activity.jsonl` |

Jeder Bereich wird defensiv gesammelt: ein fehlendes/fehlerhaftes Subsystem degradiert zu einem Fehler-Stub statt die Oberfläche zu brechen.

## Funktionen (Aktionen)

- **Plan erstellen / prüfen / starten** – `create_plan`, `inspect_plan`, `start_plan`.
- **Approval bestätigen / ablehnen** – `approve`, `reject` (über den v30.61 Safety-Layer).
- **Workflow überwachen** – `monitor_workflow`.
- **Goal Tracking anzeigen** – `goal_report`, `area_goals`.
- **Background Agents verwalten** – `manage_background_agent` (start/stop/pause/resume/run).

Aktionen schreiben in den bestehenden `runtime/native/agent_activity.jsonl`-Log.

## GUI-Panel

`agent_control/gui.py` rendert die acht Bereiche als Tabs. `AgentControlPanel` ist ein einbettbares `ttk.Frame` für die AI-Workspace-Shell; `run_gui` ist nur ein Standalone-Dev-Einstieg. Die Render-Daten kommen aus dem UI-freien `view_model()` / `build_tabs()` (testbar ohne Tkinter; Tkinter wird lazy importiert).

## Launcher-Kommandos

```
python launcher.py agent-control-center            # Übersicht (JSON)
python launcher.py agent-control-center-gui         # Panel als Fenster
python launcher.py agent-control-area <bereich>
python launcher.py agent-control-plan-create --goal TEXT
python launcher.py agent-control-plan-inspect <plan_id>
python launcher.py agent-control-plan-start <plan_id>
python launcher.py agent-control-approve <approval_id> [--by NAME]
python launcher.py agent-control-reject  <approval_id> [--by NAME]
python launcher.py agent-control-workflow <workflow_id>
python launcher.py agent-control-goal-report <goal_id>
python launcher.py agent-control-bg <agent_id> --action start|stop|pause|resume|run
```

## Tests

- `test_agent_control_gui.py` – Übersicht, alle acht Bereiche, `view_model`/`build_tabs` (UI-frei), Aktionen (Plan, Approve/Reject, Workflow, Background Agents), Logging.
- `test_agent_workspace_integration.py` – `agent_control` in Navigation/Snapshot registriert (ready), `module_payload` liefert Übersicht, Bestandsmodule bleiben erhalten.

## Qualitätsnachweis

```
python -m compileall secondbrain/native/agent_control secondbrain/native/ai_workspace/service.py launcher.py
pytest tests/test_agent_control_gui.py tests/test_agent_workspace_integration.py -q
```

Erwartung: 14 passed. Zielinterpreter Python 3.11+.

## Hinweis

Das eigentliche Tkinter-Rendering wird in dieser Umgebung nicht ausgeführt (kein `tkinter`), die Logik ist aber über das UI-freie `view_model()`/`build_tabs()` vollständig getestet. Das bestehende `agent_control_center.py` (v30.34) bleibt unangetastet; die neue Oberfläche aggregiert die späteren Agent-Subsysteme.
