# Delta v30.69 anwenden – Multi-Agent Coordination

## 1. Dateien übernehmen

Inhalt aus `SecondBrain-Agent/` in dein Projektverzeichnis `SecondBrain-Agent/` kopieren, bestehende Dateien überschreiben.

Neu:

- `secondbrain/agent/coordination/__init__.py`
- `secondbrain/agent/coordination/models.py`
- `secondbrain/agent/coordination/bus.py`
- `secondbrain/agent/coordination/shared.py`
- `secondbrain/agent/coordination/agents.py`
- `secondbrain/agent/coordination/coordinator.py`
- `tests/_coord_fakes.py`
- `tests/test_communication.py`
- `tests/test_agents.py`
- `tests/test_coordinator.py`
- `docs/releases/v30_69_multi_agent_coordination.md`

Geändert: `README_PATCH.md`, `RELEASE_NOTES.md`.

Kein Launcher-/GUI-Eingriff (Library-Ebene).

## 2. Qualität prüfen

```powershell
python -m compileall .
pytest -q
```

Gezielt:

```powershell
pytest tests/test_communication.py tests/test_agents.py tests/test_coordinator.py -q
```

Erwartung: 22 passed. Zielinterpreter Python 3.11+.

## 3. Nutzung

```python
from secondbrain.agent.coordination import Coordinator

c = Coordinator(project_root)
result = c.solve("Importiere und indexiere die Prozessdokumente")
# result: plan (Planner) -> critique (Critic/Reasoning) -> review (Reviewer)
#         -> execution (WorkflowExecutor), sofern approved und Severity != high
c.context().get("solution")          # Shared Context
c.delegate_kind("memory.store", {"text": "Fakt"})   # Task Delegation
```

## 4. Hinweise

- Keine zweite Agent Engine: die Spezialisten adaptieren `AgentPlanService`, `WorkflowExecutor`, `MemoryInjector`, `ReasoningSession`, `JobQueueService`, `GoalTracker`.
- Delegation routet nach Capability; jede Delegation wird auf dem Communication Bus protokolliert (`runtime/agent/coordination/bus.jsonl`).
- `solve` blockiert die Ausführung bei High-Severity-Kritik oder fehlender Freigabe.
