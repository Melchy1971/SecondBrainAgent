# v30.69 – Multi-Agent Coordination

## Zweck

Bestehende Agenten als Spezialisten hinter einem Coordinator orchestrieren – keine zweite Agent Engine. Ein Communication Bus, capability-basierte Task-Delegation und gemeinsamer Context/Memory/Goals ermöglichen Zusammenarbeit (Planen → Kritik → Review → Ausführen).

## Wiederverwendung (keine zweite Engine)

Jeder Spezialist ist ein dünner Adapter über einem Bestands-Subsystem:

| Spezialist | Rolle | Bestands-Subsystem |
|-----------|-------|--------------------|
| `PlannerAgent` | planner | `AgentPlanService` (v30.59) |
| `ExecutorAgent` | executor | `WorkflowExecutor` (v30.62) |
| `CriticAgent` | critic | `ReasoningSession` (v30.68) |
| `ReviewerAgent` | reviewer | deterministische Plan-Prüfungen |
| `MemoryAgent` | memory | `SharedMemory` (Memory-Store + `MemoryInjector`, v30.64) |
| `SearchAgent` | search | `SharedMemory.recall` (Memory-Injektion) |
| `ImportAgent` | import | `JobQueueService`-Snapshot (v30.44) |

## Komponenten

Modul: `secondbrain/agent/coordination/`

| Klasse | Datei | Aufgabe |
|--------|-------|---------|
| `Coordinator` | `coordinator.py` | Registrierung, Delegation, `solve`-Pipeline |
| `CoordinationWorkspace` | `coordinator.py` | Bündel aus Context/Memory/Goals/Bus |
| `CommunicationBus` | `bus.py` | synchrones Pub/Sub + Nachrichten-Log |
| `SharedContext` | `shared.py` | Blackboard (Key/Value + Historie) |
| `SharedMemory` | `shared.py` | gemeinsamer Memory-Store, Recall via Injektor |
| `SharedGoals` | `shared.py` | gemeinsame Ziele über `GoalTracker` |
| `SpecialistAgent` + 7 Agenten | `agents.py` | Adapter über Bestands-Subsysteme |
| `AgentTask` / `AgentResult` / `AgentMessage` | `models.py` | Nachrichten |

## Task Delegation

`Coordinator.delegate(task)` routet nach Capability: der erste Spezialist, dessen `capabilities` die `task.kind` abdeckt, bearbeitet sie. Jede Delegation veröffentlicht eine `task:<kind>`- und eine `result`-Nachricht auf dem Bus. Ein abstürzender Spezialist bricht den Lauf nicht ab (Fehler wird als `AgentResult.failure` gekapselt).

## Collaboration-Pipeline (`solve`)

1. **Planner** zerlegt das Ziel in einen Plan.
2. **Critic** prüft den Plan (Reasoning) → Severity low/medium/high.
3. **Reviewer** prüft Vollständigkeit → approved/notes.
4. **Executor** führt aus – nur wenn approved **und** Severity ≠ high (sonst blockiert).

Ergebnis-Summary landet im `SharedContext` (`solution`).

## Shared State

- **Shared Context:** In-Session-Blackboard; jeder Agent legt seine Ausgabe ab (`plan`, `critique`, `review`, `execution`, `solution`).
- **Shared Memory:** ein gemeinsamer Memory-Store; was ein Agent speichert, findet der nächste per Recall.
- **Shared Goals:** gemeinsame Ziele über den `GoalTracker`.

## Tests

- `test_communication.py` – Bus Pub/Sub, Log, Filter, Persistenz.
- `test_agents.py` – jeder Spezialist einzeln (Planner/Critic/Reviewer/Executor/Memory/Search/Import), Capabilities.
- `test_coordinator.py` – Delegation nach Capability, unbekannte Kind, `solve`-Pipeline (ausführen / bei High-Severity blockieren), Shared Context/Memory, Bus-Nachrichten.

## Qualitätsnachweis

```
python -m compileall secondbrain/agent/coordination
pytest tests/test_communication.py tests/test_agents.py tests/test_coordinator.py -q
```

Erwartung: 22 passed. Keine Regression in v30.61–v30.68. Zielinterpreter Python 3.11+.

## Hinweis

Deterministisch, kein LLM-Aufruf: der Coordinator strukturiert die Zusammenarbeit der bestehenden Agenten und macht sie über Bus + Shared Context auditierbar. Kein Launcher-/GUI-Eingriff (Library-Ebene).
