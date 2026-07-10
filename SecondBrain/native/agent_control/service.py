"""v30.66 Native Agent Control - aggregation service.

The single agent-control surface inside the native AI Workspace. It does not
re-implement any agent subsystem; it composes read models from the existing
ones (Planner, Workflow Engine, Background Agents, Approval/Safety layer, Goal
Tracking) plus the audit and log trails, and exposes the actions the GUI needs.

Every area is collected defensively: a missing or failing subsystem degrades to
an error stub instead of breaking the whole surface (same contract as
``AIWorkspaceService.module_payload``).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

AREAS = (
    ("agents", "Agenten"),
    ("plans", "Pläne"),
    ("workflows", "Workflows"),
    ("background_agents", "Background Agents"),
    ("approvals", "Approvals"),
    ("goals", "Goals"),
    ("audit", "Audit"),
    ("logs", "Logs"),
)


def _tail_jsonl(path: Path, limit: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows[-max(1, limit):]


class AgentControlService:
    VERSION = "v30.66"

    def __init__(self, project_root: str | Path = "."):
        self.project_root = Path(project_root).resolve()
        self.runtime_native = self.project_root / "runtime" / "native"
        self.activity_path = self.runtime_native / "agent_activity.jsonl"

    # -- lazy subsystem accessors -----------------------------------------
    def _planner(self):
        from secondbrain.agent.planner import AgentPlanService
        return AgentPlanService(self.project_root)

    def _workflow_store(self):
        from secondbrain.agent.workflow.store import WorkflowStore
        return WorkflowStore(self.project_root)

    def _supervisor(self):
        from secondbrain.agent.background_agents import AgentSupervisor
        return AgentSupervisor.for_project(self.project_root)

    def _safety(self):
        from secondbrain.agent.safety import SafetyService
        return SafetyService(self.project_root)

    def _goals(self):
        from secondbrain.agent.goals import GoalTracker
        return GoalTracker.for_project(self.project_root)

    # -- areas -------------------------------------------------------------
    def _safe(self, fn):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - area must not crash the surface
            return {"ok": False, "status": "area_error", "error": type(exc).__name__, "detail": str(exc)}

    def area_agents(self) -> dict[str, Any]:
        def build():
            plans = self._planner().list()
            supervisor = self._supervisor()
            agents = supervisor.list()
            wf = self._workflow_store().list()
            active_bg = [a for a in agents if a["state"] == "ACTIVE"]
            return {
                "ok": True,
                "plans_total": len(plans),
                "workflows_total": len(wf),
                "background_agents_total": len(agents),
                "background_agents_active": len(active_bg),
            }
        return self._safe(build)

    def area_plans(self, *, limit: int = 50) -> dict[str, Any]:
        def build():
            plans = self._planner().list()
            items = []
            for plan in plans[:limit]:
                d = plan.to_dict() if hasattr(plan, "to_dict") else dict(plan)
                steps = d.get("steps", [])
                done = sum(1 for s in steps if s.get("status") == "completed")
                waiting = sum(1 for s in steps if s.get("status") == "waiting_approval")
                failed = sum(1 for s in steps if s.get("status") == "failed")
                deps = sum(len(s.get("dependencies") or []) for s in steps)
                items.append({
                    "id": d["id"], "goal": d.get("goal", ""), "status": d.get("status"),
                    "steps": len(steps), "steps_completed": done,
                    "requires_approval": any(s.get("requires_approval") for s in steps),
                    "approval_gates": sum(1 for s in steps if s.get("requires_approval")),
                    "waiting_approval": waiting,
                    "failed_steps": failed,
                    "dependencies": deps,
                    "maximum_risk": (d.get("metadata") or {}).get("maximum_risk", "low"),
                })
            return {"ok": True, "count": len(items), "plans": items}
        return self._safe(build)

    def area_workflows(self, *, limit: int = 50) -> dict[str, Any]:
        def build():
            checkpoints = self._workflow_store().list()
            items = []
            for cp in checkpoints[:limit]:
                runs = cp.runs()
                done = sum(1 for r in runs.values() if r.status == "completed")
                items.append({
                    "workflow_id": cp.workflow_id, "objective": cp.objective,
                    "state": cp.state.value, "steps": len(cp.steps), "steps_completed": done,
                })
            return {"ok": True, "count": len(items), "workflows": items}
        return self._safe(build)

    def area_background_agents(self) -> dict[str, Any]:
        def build():
            agents = self._supervisor().list()
            return {"ok": True, "count": len(agents), "agents": agents}
        return self._safe(build)

    def area_approvals(self) -> dict[str, Any]:
        def build():
            all_rows = self._safety().list()
            pending = [row for row in all_rows if row.get("status") == "pending"]
            deferred = [row for row in all_rows if row.get("status") == "deferred"]
            open_items = pending + deferred
            return {
                "ok": True,
                "pending": len(pending),
                "deferred": len(deferred),
                "open": len(open_items),
                "approvals": open_items,
            }
        return self._safe(build)

    def area_goals(self) -> dict[str, Any]:
        def build():
            tracker = self._goals()
            goals = tracker.list()
            snap = tracker.dashboard_snapshot()
            return {"ok": True, "count": len(goals), "goals": goals,
                    "avg_progress": snap.get("avg_progress", 0.0), "at_risk": snap.get("at_risk", [])}
        return self._safe(build)

    def area_audit(self, *, limit: int = 20) -> dict[str, Any]:
        def build():
            trails = {
                "approvals": self.runtime_native / "action_audit.jsonl",
                "workflows": self.project_root / "runtime" / "agent" / "workflows" / "workflow_audit.jsonl",
                "memory_injection": self.project_root / "runtime" / "agent" / "memory_injection" / "audit.jsonl",
            }
            out: dict[str, Any] = {"ok": True, "trails": {}}
            for name, path in trails.items():
                rows = _tail_jsonl(path, limit)
                out["trails"][name] = {"count": len(rows), "latest": list(reversed(rows))}
            return out
        return self._safe(build)

    def area_logs(self, *, limit: int = 40) -> dict[str, Any]:
        def build():
            rows = _tail_jsonl(self.activity_path, limit)
            return {"ok": True, "count": len(rows), "logs": list(reversed(rows))}
        return self._safe(build)

    # -- composed views ----------------------------------------------------
    def area(self, name: str, **kwargs) -> dict[str, Any]:
        method = {
            "agents": self.area_agents,
            "plans": self.area_plans,
            "workflows": self.area_workflows,
            "background_agents": self.area_background_agents,
            "approvals": self.area_approvals,
            "goals": self.area_goals,
            "audit": self.area_audit,
            "logs": self.area_logs,
        }.get(name)
        if method is None:
            return {"ok": False, "status": "unknown_area", "area": name}
        return method(**kwargs)

    def overview(self) -> dict[str, Any]:
        agents = self.area_agents()
        approvals = self.area_approvals()
        goals = self.area_goals()
        workflows = self.area_workflows()
        return {
            "ok": True,
            "version": self.VERSION,
            "project_root": str(self.project_root),
            "areas": [aid for aid, _ in AREAS],
            "summary": {
                "plans": agents.get("plans_total", 0),
                "workflows": agents.get("workflows_total", 0),
                "background_agents": agents.get("background_agents_total", 0),
                "background_agents_active": agents.get("background_agents_active", 0),
                "approvals_pending": approvals.get("pending", 0),
                "goals": goals.get("count", 0),
                "goals_at_risk": len(goals.get("at_risk", [])),
                "goals_avg_progress": goals.get("avg_progress", 0.0),
                "workflows_running": sum(1 for w in workflows.get("workflows", []) if w["state"] == "RUNNING"),
            },
        }

    def view_model(self) -> dict[str, Any]:
        """UI-free model the native GUI renders (one entry per area)."""
        areas = []
        for aid, title in AREAS:
            payload = self.area(aid)
            areas.append({"id": aid, "title": title, "ok": payload.get("ok", False), "data": payload})
        return {"ok": True, "version": self.VERSION, "areas": areas,
                "overview": self.overview()}

    # -- actions -----------------------------------------------------------
    def create_plan(self, goal: str, *, workspace_id: str | None = None) -> dict[str, Any]:
        plan = self._planner().create(goal, workspace_id=workspace_id)
        d = plan.to_dict()
        self._log("plan_created", {"plan_id": d["id"], "goal": goal})
        return {"ok": True, "plan": d}

    def inspect_plan(self, plan_id: str) -> dict[str, Any]:
        plan = self._planner().load(plan_id)
        d = plan.to_dict()
        steps = d.get("steps", [])
        return {
            "ok": True,
            "plan": d,
            "checks": {
                "steps": len(steps),
                "requires_approval": sum(1 for s in steps if s.get("requires_approval")),
                "high_risk": sum(1 for s in steps if s.get("risk_level") in {"high", "critical"}),
                "status": d.get("status"),
            },
        }

    def explain_plan(self, plan_id: str) -> dict[str, Any]:
        payload = self._planner().explain(plan_id)
        self._log("plan_explained", {"plan_id": plan_id, "step_count": payload.get("step_count", 0)})
        return payload

    def start_plan(self, plan_id: str) -> dict[str, Any]:
        plan = self._planner().resume(plan_id)
        d = plan.to_dict()
        self._log("plan_started", {"plan_id": plan_id, "status": d.get("status")})
        return {"ok": True, "plan": d}

    def approve(self, approval_id: str, *, decided_by: str = "user") -> dict[str, Any]:
        decision = self._safety().approve(approval_id, decided_by=decided_by)
        self._log("approval_approved", {"approval_id": approval_id})
        return {"ok": decision.ok, **decision.to_dict()}

    def reject(self, approval_id: str, *, decided_by: str = "user") -> dict[str, Any]:
        decision = self._safety().reject(approval_id, decided_by=decided_by)
        self._log("approval_rejected", {"approval_id": approval_id})
        return {"ok": decision.ok, **decision.to_dict()}

    def defer(self, approval_id: str, *, decided_by: str = "user", until: str = "", note: str = "") -> dict[str, Any]:
        decision = self._safety().defer(approval_id, decided_by=decided_by, until=until, note=note)
        self._log("approval_deferred", {"approval_id": approval_id, "until": until})
        return {"ok": decision.ok, **decision.to_dict()}

    def monitor_workflow(self, workflow_id: str) -> dict[str, Any]:
        cp = self._workflow_store().load(workflow_id)
        if cp is None:
            return {"ok": False, "error": f"unknown_workflow:{workflow_id}"}
        runs = cp.runs()
        return {
            "ok": True,
            "workflow_id": cp.workflow_id,
            "state": cp.state.value,
            "objective": cp.objective,
            "steps": len(cp.steps),
            "steps_completed": sum(1 for r in runs.values() if r.status == "completed"),
            "step_runs": cp.step_runs,
        }

    def goal_report(self, goal_id: str) -> dict[str, Any]:
        return {"ok": True, **self._goals().report(goal_id)}

    def manage_background_agent(self, agent_id: str, action: str) -> dict[str, Any]:
        supervisor = self._supervisor()
        action = action.lower()
        fn = {
            "start": supervisor.start, "stop": supervisor.stop, "pause": supervisor.pause,
            "resume": supervisor.resume,
        }.get(action)
        if fn is not None:
            agent = fn(agent_id)
            self._log("background_agent_action", {"agent_id": agent_id, "action": action})
            return {"ok": True, "agent": agent.to_dict()}
        if action == "run":
            run = supervisor.run_agent(agent_id)
            self._log("background_agent_action", {"agent_id": agent_id, "action": "run"})
            return {"ok": True, "run": run.to_dict()}
        return {"ok": False, "error": f"unknown_action:{action}"}

    # -- helpers -----------------------------------------------------------
    def _log(self, event: str, payload: dict[str, Any]) -> None:
        self.runtime_native.mkdir(parents=True, exist_ok=True)
        import time
        row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "event": event, "source": "agent_control", "payload": payload}
        with self.activity_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def status(self) -> dict[str, Any]:
        return self.overview()
