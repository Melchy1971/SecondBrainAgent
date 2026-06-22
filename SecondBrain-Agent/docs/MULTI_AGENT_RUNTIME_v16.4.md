# SecondBrain OS v16.4 – Multi-Agent Runtime

## Ziel
v16.4 ergänzt ein strukturiertes Multi-Agent-System.

## Agenten
- Supervisor Agent
- Planner Agent
- Research Agent
- Execution Agent
- Review Agent
- Memory Agent
- Improvement Agent

## Ablauf
```text
Task
→ Supervisor
→ Planner
→ Research
→ Execution
→ Review
→ Memory
→ Improvement Backlog
```

## Befehle
```powershell
python launcher.py agent16-migrate
python launcher.py agent16-status
python launcher.py agent16-agents
python launcher.py agent16-task-create "Sprint" "Plane den nächsten Sprint"
python launcher.py agent16-tasks
python launcher.py agent16-plan <TASK_ID>
python launcher.py agent16-run <TASK_ID>
python launcher.py agent16-messages --task-id <TASK_ID>
python launcher.py agent16-results --task-id <TASK_ID>
python launcher.py agent16-reviews --task-id <TASK_ID>
python launcher.py agent16-memory
python launcher.py agent16-backlog
```

## Grenzen
- Agentenlogik ist deterministisch.
- Keine echte LLM-Planung.
- Keine echten Tool-Aufrufe.
- Approval ist als Status modelliert, noch nicht mit Security-Gate verbunden.
