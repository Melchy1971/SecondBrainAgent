"""v30.62 Agent Workflow Engine - service facade.

Thin application service used by the launcher CLI. Wires the real reused
subsystems via :meth:`WorkflowExecutor.for_project` and converts step specs
(plain dicts, e.g. from JSON) into :class:`WorkflowStep` objects.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from secondbrain.agent.workflow_models import WorkflowStep

from .executor import WorkflowExecutor


def step_from_spec(spec: dict[str, Any], index: int) -> WorkflowStep:
    return WorkflowStep(
        id=str(spec.get("id") or f"step_{index + 1}"),
        name=str(spec.get("name") or spec.get("id") or f"Step {index + 1}"),
        tool_name=spec.get("tool_name") or spec.get("tool"),
        input=dict(spec.get("input", {})),
        dependencies=list(spec.get("dependencies", [])),
        timeout_seconds=int(spec.get("timeout_seconds", 300)),
        max_retries=int(spec.get("max_retries", 3)),
        requires_approval=bool(spec.get("requires_approval", False)),
    )


class WorkflowService:
    def __init__(self, project_root: str | Path, *, executor: WorkflowExecutor | None = None, **overrides: Any):
        self.project_root = Path(project_root).resolve()
        self.executor = executor or WorkflowExecutor.for_project(self.project_root, **overrides)

    def create(self, objective: str, steps: Iterable[dict[str, Any]], *, workflow_id: str | None = None) -> dict[str, Any]:
        parsed = [step_from_spec(spec, i) for i, spec in enumerate(steps)]
        cp = self.executor.create(objective, parsed, workflow_id=workflow_id)
        return {"ok": True, **self.executor.status(cp.workflow_id)}

    def run(self, workflow_id: str) -> dict[str, Any]:
        self.executor.run(workflow_id)
        return {"ok": True, **self.executor.status(workflow_id)}

    def resume(self, workflow_id: str) -> dict[str, Any]:
        self.executor.resume(workflow_id)
        return {"ok": True, **self.executor.status(workflow_id)}

    def cancel(self, workflow_id: str) -> dict[str, Any]:
        self.executor.cancel(workflow_id)
        return {"ok": True, **self.executor.status(workflow_id)}

    def status(self, workflow_id: str) -> dict[str, Any]:
        return {"ok": True, **self.executor.status(workflow_id)}

    def list(self) -> dict[str, Any]:
        items = self.executor.list()
        return {"ok": True, "count": len(items), "workflows": items}

    def audit(self, workflow_id: str | None = None, *, limit: int = 200) -> dict[str, Any]:
        events = self.executor.audit_events(workflow_id, limit=limit)
        return {"ok": True, "count": len(events), "events": events}

    def prepare_rollback(self, workflow_id: str) -> dict[str, Any]:
        return {"ok": True, **self.executor.prepare_rollback(workflow_id)}
