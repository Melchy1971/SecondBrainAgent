from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any
import json
import time
import uuid

from .autonomous_agent_v110 import ToolHost


@dataclass
class WorkflowStep:
    step_id: str
    name: str
    action: str
    payload: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    status: str = "pending"
    result: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    started_at: float | None = None
    finished_at: float | None = None


@dataclass
class WorkflowDefinition:
    workflow_id: str
    name: str
    description: str = ""
    steps: list[WorkflowStep] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowRun:
    run_id: str
    workflow: WorkflowDefinition
    status: str = "created"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    outputs: dict[str, Any] = field(default_factory=dict)


class WorkflowStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")

    def _load(self) -> dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError:
            backup = self.path.with_suffix('.json.corrupt')
            self.path.replace(backup)
            self.path.write_text("{}", encoding="utf-8")
            return {}

    def save(self, run: WorkflowRun) -> None:
        data = self._load()
        run.updated_at = time.time()
        data[run.run_id] = asdict(run)
        tmp = self.path.with_suffix('.json.tmp')
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
        tmp.replace(self.path)

    def list(self) -> list[WorkflowRun]:
        return [self._run_from_dict(v) for v in self._load().values()]

    def get(self, run_id: str) -> WorkflowRun:
        data = self._load()
        if run_id not in data:
            raise KeyError("unknown_workflow_run")
        return self._run_from_dict(data[run_id])

    @staticmethod
    def _run_from_dict(data: dict[str, Any]) -> WorkflowRun:
        wf_raw = data["workflow"]
        steps = [WorkflowStep(**s) for s in wf_raw.get("steps", [])]
        wf = WorkflowDefinition(
            workflow_id=wf_raw["workflow_id"],
            name=wf_raw["name"],
            description=wf_raw.get("description", ""),
            steps=steps,
            metadata=dict(wf_raw.get("metadata", {})),
        )
        return WorkflowRun(
            run_id=data["run_id"],
            workflow=wf,
            status=data.get("status", "created"),
            created_at=float(data.get("created_at", time.time())),
            updated_at=float(data.get("updated_at", time.time())),
            outputs=dict(data.get("outputs", {})),
        )


class WorkflowEngine:
    """Deterministic workflow executor for v11.2.

    Constraints:
    - stdlib only
    - persistent workflow runs
    - dependency-aware step execution
    - tool execution delegated to the existing ToolHost/security surface
    """

    def __init__(self, runtime_dir: str | Path, tool_host: ToolHost):
        self.runtime_dir = Path(runtime_dir)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.tool_host = tool_host
        self.store = WorkflowStore(self.runtime_dir / "workflow_runs_v112.json")

    def create_run(self, workflow: WorkflowDefinition) -> WorkflowRun:
        run = WorkflowRun(run_id=uuid.uuid4().hex, workflow=workflow)
        self.store.save(run)
        return run

    def run(self, workflow: WorkflowDefinition) -> WorkflowRun:
        run = self.create_run(workflow)
        return self.execute(run.run_id)

    def execute(self, run_id: str) -> WorkflowRun:
        run = self.store.get(run_id)
        run.status = "running"
        self.store.save(run)

        while True:
            pending = [s for s in run.workflow.steps if s.status == "pending"]
            if not pending:
                break
            executable = [s for s in pending if all(self._step_by_id(run, dep).status == "done" for dep in s.depends_on)]
            if not executable:
                run.status = "blocked"
                run.outputs["reason"] = "unresolved_dependencies"
                self.store.save(run)
                return run
            for step in executable:
                step.status = "running"
                step.started_at = time.time()
                self.store.save(run)
                outcome = self.tool_host.execute(step.action, self._resolve_payload(step.payload, run.outputs))
                step.result = outcome
                step.finished_at = time.time()
                if outcome.get("ok"):
                    step.status = "done"
                    run.outputs[step.name] = outcome.get("result", outcome)
                else:
                    step.status = "blocked" if outcome.get("blocked") else "failed"
                    step.error = str(outcome.get("reason", "unknown_error"))
                    run.status = step.status
                    run.outputs["failed_step"] = step.name
                    run.outputs["error"] = step.error
                    self.store.save(run)
                    return run
                self.store.save(run)

        run.status = "completed" if all(s.status == "done" for s in run.workflow.steps) else "needs_review"
        self.store.save(run)
        return run

    def status(self) -> dict[str, Any]:
        runs = self.store.list()
        by_status: dict[str, int] = {}
        for run in runs:
            by_status[run.status] = by_status.get(run.status, 0) + 1
        return {"runs": len(runs), "by_status": by_status, "store": str(self.store.path)}

    @staticmethod
    def _step_by_id(run: WorkflowRun, step_id: str) -> WorkflowStep:
        for step in run.workflow.steps:
            if step.step_id == step_id:
                return step
        raise KeyError(f"unknown_step_dependency:{step_id}")

    @staticmethod
    def _resolve_payload(payload: dict[str, Any], outputs: dict[str, Any]) -> dict[str, Any]:
        resolved: dict[str, Any] = {}
        for key, value in payload.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                path = value[2:-1].split(".")
                current: Any = outputs
                for part in path:
                    if isinstance(current, dict):
                        current = current.get(part)
                    else:
                        current = None
                resolved[key] = current
            else:
                resolved[key] = value
        return resolved


def step(name: str, action: str, payload: dict[str, Any] | None = None, depends_on: list[str] | None = None) -> WorkflowStep:
    return WorkflowStep(step_id=uuid.uuid4().hex, name=name, action=action, payload=payload or {}, depends_on=depends_on or [])


def workflow_summary(run: WorkflowRun) -> dict[str, Any]:
    return {
        "run_id": run.run_id,
        "status": run.status,
        "workflow": run.workflow.name,
        "steps": [
            {"name": s.name, "action": s.action, "status": s.status, "error": s.error}
            for s in run.workflow.steps
        ],
        "outputs": run.outputs,
    }
