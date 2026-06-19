# SecondBrain OS v11.7 Automation & Scheduler Layer

## Ziel
Persistente Automationen für wiederkehrende Aufgaben, einmalige Ausführungen und sichere Brücken zu API, Agent, Workflow, RAG, Capture und Notifications.

## Befehle

```powershell
python launcher.py automation-status
python launcher.py automation-tasks
python launcher.py automation-runs
python launcher.py automation-every "Status Watch" api.dispatch --minutes 60 --payload "{\"method\":\"GET\",\"path\":\"/status\"}"
python launcher.py automation-once "Capture Test" capture --payload "{\"title\":\"Test\",\"text\":\"Automation läuft\"}"
python launcher.py automation-run-due
python launcher.py automation-run <TASK_ID>
python launcher.py automation-disable <TASK_ID>
python launcher.py automation-enable <TASK_ID>
```

## Targets

- `api.dispatch`
- `agent.run`
- `workflow.run`
- `rag.answer`
- `capture`
- `notify`

## Persistenz

```text
data/runtime/automation/tasks.json
data/runtime/automation/runs.jsonl
```

## Sicherheitsmodell
Der Scheduler führt keine beliebigen Shell-Kommandos aus. Er nutzt ausschließlich registrierte Runtime-Ziele. Riskante Aktionen laufen weiter über API-, Agent- und Governance-Gates.
