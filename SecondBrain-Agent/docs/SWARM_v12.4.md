# SecondBrain OS v12.4 – Multi-Agent Swarm

## Ziel

v12.4 integriert einen deterministischen Multi-Agent-Swarm in den bestehenden v12.3-Projektstand.

## Komponenten

- Swarm Kernel
- Agent Registry
- Shared Context Store
- Agent Message Bus
- Supervisor Agent
- Planner Agent
- Research Agent
- Executor Agent
- Reviewer Agent
- Memory Curator Agent
- Consensus Engine
- Recovery Engine

## Agentenfluss

```text
Task
↓
Supervisor
↓
Planner
↓
Researcher
↓
Executor
↓
Reviewer
↓
Memory Curator
↓
Consensus
↓
Result
```

## Launcher-Kommandos

```powershell
python launcher.py swarm-status
python launcher.py swarm-agents
python launcher.py swarm-run "Plane mein Tischtennistraining"
python launcher.py swarm-task <TASK_ID>
python launcher.py swarm-history
python launcher.py swarm-consensus <TASK_ID>
python launcher.py swarm-recover <TASK_ID>
python launcher.py swarm-stop <TASK_ID>
```

## Persistenz

```text
data/runtime/swarm_v124/
├── agents.json
├── tasks.json
├── plans.json
├── messages.json
├── results.json
├── history.json
├── contexts.json
├── context_history.json
├── consensus.json
└── recovery.json
```

## Event-Bus Topics

```text
swarm.task.created
swarm.plan.created
swarm.research.completed
swarm.execution.completed
swarm.review.completed
swarm.memory.updated
swarm.failed
swarm.message.created
```

## Tool Registry

Neue Tools:

```text
swarm.status
swarm.agents
swarm.run
swarm.task
swarm.consensus
```

## Sicherheitsgrenze

v12.4 führt standardmäßig deterministische Safe Execution aus. Echte Tool-Ausführung bleibt an die vorhandene Tool Registry, Scopes und Approval-Mechanismen gebunden.
