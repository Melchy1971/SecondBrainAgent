from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Callable
import json
import time
import uuid

@dataclass
class AgentGoal:
    objective: str
    constraints: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    max_steps: int = 5

@dataclass
class AgentStep:
    step_id: str
    phase: str
    action: str
    payload: dict[str, Any] = field(default_factory=dict)
    status: str = "planned"
    result: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

@dataclass
class AgentRun:
    run_id: str
    goal: AgentGoal
    status: str = "created"
    steps: list[AgentStep] = field(default_factory=list)
    observations: list[dict[str, Any]] = field(default_factory=list)
    verification: dict[str, Any] = field(default_factory=dict)
    learnings: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

class AgentRunStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")

    def save(self, run: AgentRun) -> None:
        data = self._load()
        run.updated_at = time.time()
        data[run.run_id] = self._run_to_dict(run)
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def get(self, run_id: str) -> AgentRun:
        data = self._load()
        if run_id not in data:
            raise KeyError("unknown_run_id")
        return self._run_from_dict(data[run_id])

    def list(self) -> list[AgentRun]:
        return [self._run_from_dict(v) for v in self._load().values()]

    def _load(self) -> dict[str, Any]:
        return json.loads(self.path.read_text(encoding="utf-8") or "{}")

    @staticmethod
    def _run_to_dict(run: AgentRun) -> dict[str, Any]:
        return asdict(run)

    @staticmethod
    def _run_from_dict(data: dict[str, Any]) -> AgentRun:
        goal = AgentGoal(**data["goal"])
        steps = [AgentStep(**s) for s in data.get("steps", [])]
        return AgentRun(
            run_id=data["run_id"], goal=goal, status=data.get("status", "created"),
            steps=steps, observations=list(data.get("observations", [])),
            verification=dict(data.get("verification", {})), learnings=list(data.get("learnings", [])),
            created_at=float(data.get("created_at", time.time())), updated_at=float(data.get("updated_at", time.time()))
        )

class DeterministicPlanner:
    """Rule-based v11.0 planner. It is intentionally deterministic and auditable.
    LLM planning can be added behind this interface later.
    """
    def plan(self, goal: AgentGoal, observations: list[dict[str, Any]]) -> list[AgentStep]:
        objective = goal.objective.strip()
        lower = objective.lower()
        steps: list[AgentStep] = []
        def add(phase: str, action: str, payload: dict[str, Any]):
            if len(steps) < max(1, int(goal.max_steps)):
                steps.append(AgentStep(step_id=uuid.uuid4().hex, phase=phase, action=action, payload=payload))
        if any(x in lower for x in ["sync", "synchron", "connector", "email", "kalender", "dateien"]):
            add("execute", "connectors.sync", {})
        elif any(x in lower for x in ["dokument", "doku", "zusammenfassung", "notiz", "plan", "bericht"]):
            add("observe", "rag.search", {"query": objective, "limit": 5})
            add("execute", "rag.answer", {"query": objective, "limit": 5})
            add("execute", "desktop.quick_capture", {"title": "Agent Ergebnis", "text": f"Ziel: {objective}\n\nErgebnis wird nach Ausführung ergänzt."})
        else:
            add("execute", "ai.ask", {"task": "agent", "prompt": objective})
        add("verify", "agent.verify", {"objective": objective})
        return steps

class ToolHost:
    def __init__(self):
        self.handlers: dict[str, Callable[[dict[str, Any]], Any]] = {}
    def register(self, action: str, handler: Callable[[dict[str, Any]], Any]) -> None:
        self.handlers[action] = handler
    def execute(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        if action not in self.handlers:
            return {"ok": False, "reason": "missing_tool", "action": action}
        try:
            result = self.handlers[action](payload or {})
            if isinstance(result, dict) and "ok" in result:
                return result
            return {"ok": True, "result": result}
        except PermissionError as exc:
            return {"ok": False, "reason": str(exc), "blocked": True}
        except Exception as exc:
            return {"ok": False, "reason": str(exc)}

class AutonomousAgentRuntime:
    def __init__(self, runtime_dir: str | Path, tool_host: ToolHost | None = None, planner: DeterministicPlanner | None = None):
        self.runtime_dir = Path(runtime_dir)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.store = AgentRunStore(self.runtime_dir / "agent_runs_v110.json")
        self.tool_host = tool_host or ToolHost()
        self.planner = planner or DeterministicPlanner()
        self.tool_host.register("agent.verify", self._verify_tool)

    def create_run(self, objective: str, *, constraints: list[str] | None = None, context: dict[str, Any] | None = None, max_steps: int = 5) -> AgentRun:
        run = AgentRun(run_id=uuid.uuid4().hex, goal=AgentGoal(objective=objective, constraints=constraints or [], context=context or {}, max_steps=max_steps))
        self.store.save(run)
        return run

    def run_once(self, objective: str, *, constraints: list[str] | None = None, context: dict[str, Any] | None = None, max_steps: int = 5) -> AgentRun:
        run = self.create_run(objective, constraints=constraints, context=context, max_steps=max_steps)
        return self.execute_run(run.run_id)

    def execute_run(self, run_id: str) -> AgentRun:
        run = self.store.get(run_id)
        run.status = "observing"
        run.observations.append({"ts": time.time(), "type": "goal_received", "objective": run.goal.objective, "constraints": run.goal.constraints})
        self.store.save(run)

        run.status = "planning"
        run.steps = self.planner.plan(run.goal, run.observations)
        self.store.save(run)

        run.status = "executing"
        for step in run.steps:
            step.status = "running"; step.updated_at = time.time(); self.store.save(run)
            outcome = self.tool_host.execute(step.action, step.payload)
            step.result = outcome if isinstance(outcome, dict) else {"ok": True, "result": outcome}
            step.status = "done" if step.result.get("ok") else ("blocked" if step.result.get("blocked") else "failed")
            step.error = "" if step.result.get("ok") else str(step.result.get("reason", "unknown_error"))
            step.updated_at = time.time()
            if step.status in {"blocked", "failed"}:
                run.status = step.status
                run.verification = {"ok": False, "reason": step.error, "failed_step": step.action}
                run.learnings.append(f"Tool {step.action} ended with {step.status}: {step.error}")
                self.store.save(run)
                return run
            self.store.save(run)

        run.status = "verifying"
        run.verification = self.verify(run)
        run.status = "completed" if run.verification.get("ok") else "needs_review"
        run.learnings.extend(self.learn(run))
        self.store.save(run)
        return run

    def verify(self, run: AgentRun) -> dict[str, Any]:
        if not run.steps:
            return {"ok": False, "reason": "no_steps"}
        failed = [s for s in run.steps if s.status != "done"]
        if failed:
            return {"ok": False, "reason": "step_not_done", "failed": [s.action for s in failed]}
        return {"ok": True, "steps": len(run.steps), "objective": run.goal.objective}

    def learn(self, run: AgentRun) -> list[str]:
        actions = ", ".join(s.action for s in run.steps)
        return [f"Completed objective with {len(run.steps)} steps: {actions}"]

    def status(self) -> dict[str, Any]:
        runs = self.store.list()
        by_status: dict[str, int] = {}
        for r in runs:
            by_status[r.status] = by_status.get(r.status, 0) + 1
        return {"runs": len(runs), "by_status": by_status, "store": str(self.store.path)}

    def _verify_tool(self, payload: dict[str, Any]) -> dict[str, Any]:
        objective = str(payload.get("objective", "")).strip()
        return {"ok": bool(objective), "objective": objective}

def run_to_summary(run: AgentRun) -> dict[str, Any]:
    return {
        "run_id": run.run_id,
        "status": run.status,
        "objective": run.goal.objective,
        "steps": [{"phase": s.phase, "action": s.action, "status": s.status, "error": s.error, "result": s.result} for s in run.steps],
        "verification": run.verification,
        "learnings": run.learnings,
    }
