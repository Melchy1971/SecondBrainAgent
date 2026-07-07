# APPLY DELTA v30.59 – Agent Planner

## Ergebnis

Der bestehende Agent-Pfad besitzt jetzt einen persistenten, validierten und risikobewerteten Planner. Es wurde keine zweite Agent-, Queue-, Approval- oder Memory-Architektur eingeführt.

## Komponenten

- `AgentPlan`, `AgentStep`, `PlanStatus`
- `PlanBuilder`, `PlanValidator`, `PlanRiskAnalyzer`, `PlanPersistence`
- `AgentPlanService` integriert AgentCore, ChatService, Command Center, Memory, Native Job Queue und Native Approval Queue

Persistenz: `runtime/agent/plans.json`. Aktivierte Schritte werden als `agent`-Jobs in die vorhandene Native Job Queue geschrieben. Riskante Schritte bleiben bis zur vorhandenen Approval-Entscheidung blockiert.

## Launcher

```powershell
python launcher.py agent-plan-create "Status prüfen; danach Projektlage erklären"
python launcher.py agent-plan-list
python launcher.py agent-plan-show PLAN_ID
python launcher.py agent-plan-cancel PLAN_ID
python launcher.py agent-plan-resume PLAN_ID
```

## Validierung

```powershell
python -m compileall .
pytest -q
python launcher.py repo-doctor
```
