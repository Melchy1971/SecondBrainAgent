"""v30.62 Agent Workflow Engine - WorkflowExecutor.

Turns a multi-step agent plan into an executable, crash-recoverable workflow.

Reused subsystems (all injectable, no re-implementation):
* Tool Registry  - runs each step's tool.
* Approval Layer - the v30.61 SafetyService / native approval queue for
  ``requires_approval`` steps. No second approval queue.
* Job Queue      - each workflow is mirrored as one ``agent`` job.
* Notification Center - approval-needed / failure / completion notices.
* Memory         - optional sink fed with completed-step and outcome facts.

State is checkpointed to disk after every step, which is what makes
``resume_after_crash`` and ``resume_after_approval`` possible.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable
from uuid import uuid4

from secondbrain.agent.workflow_models import WorkflowStep

from .audit import WorkflowAudit
from .models import (
    STEP_COMPLETED,
    STEP_FAILED,
    STEP_PENDING,
    STEP_RUNNING,
    STEP_WAITING_APPROVAL,
    StepRun,
    Workflow,
    WorkflowCheckpoint,
    WorkflowState,
)
from .recovery import FAIL_FAST, ROLLBACK, WAIT_FOR_APPROVAL, WorkflowRecovery
from .store import WorkflowStore


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _topological_order(steps: list[WorkflowStep]) -> list[WorkflowStep]:
    """Order steps so dependencies precede dependents (stable, deterministic)."""

    by_id = {s.id: s for s in steps}
    resolved: list[WorkflowStep] = []
    seen: set[str] = set()
    temp: set[str] = set()

    def visit(step: WorkflowStep) -> None:
        if step.id in seen:
            return
        if step.id in temp:
            raise ValueError(f"cyclic_dependency:{step.id}")
        temp.add(step.id)
        for dep in step.dependencies:
            if dep in by_id:
                visit(by_id[dep])
        temp.discard(step.id)
        seen.add(step.id)
        resolved.append(step)

    for step in steps:
        visit(step)
    return resolved


class WorkflowExecutor:
    def __init__(
        self,
        project_root: str | Path,
        *,
        tool_registry: Any | None = None,
        tool_runner: Callable[[WorkflowStep, bool], Any] | None = None,
        safety: Any | None = None,
        jobs: Any | None = None,
        notifications: Any | None = None,
        memory_sink: Callable[[dict[str, Any]], None] | None = None,
        actor: str = "agent",
    ):
        self.project_root = Path(project_root).resolve()
        self.store = WorkflowStore(self.project_root)
        self.audit = WorkflowAudit(self.project_root)
        self.recovery = WorkflowRecovery()
        self.tool_registry = tool_registry
        self._tool_runner = tool_runner
        self.safety = safety
        self.jobs = jobs
        self.notifications = notifications
        self.memory_sink = memory_sink
        self.actor = actor

    # -- construction wiring the real reused subsystems --------------------
    @classmethod
    def for_project(cls, project_root: str | Path, *, actor: str = "agent", **overrides: Any) -> "WorkflowExecutor":
        root = Path(project_root).resolve()
        from secondbrain.agent.safety import SafetyService
        from secondbrain.native.job_queue_center.service import JobQueueService
        from secondbrain.native.notification_center.service import NotificationCenterService

        defaults: dict[str, Any] = {
            "safety": SafetyService(root),
            "jobs": JobQueueService(root=root),
            "notifications": NotificationCenterService(root),
        }
        try:
            from secondbrain.agent.tool_registry import ToolRegistry

            defaults["tool_registry"] = ToolRegistry(root / "runtime" / "tools_v121")
        except Exception:
            defaults["tool_registry"] = None
        defaults.update(overrides)
        return cls(root, actor=actor, **defaults)

    # -- lifecycle ---------------------------------------------------------
    def create(self, objective: str, steps: Iterable[WorkflowStep], *, workflow_id: str | None = None) -> WorkflowCheckpoint:
        ordered = _topological_order(list(steps))
        wf = Workflow(id=workflow_id or f"wf_{uuid4().hex[:12]}", objective=objective, steps=ordered)
        cp = WorkflowCheckpoint(
            workflow_id=wf.id,
            objective=objective,
            state=WorkflowState.PENDING,
            cursor=0,
            steps=wf.to_dict()["steps"],
            step_runs={s.id: StepRun(step_id=s.id).to_dict() for s in ordered},
        )
        if self.jobs is not None:
            job = self.jobs.add_job("agent", objective or wf.id, payload={"workflow_id": wf.id})
            cp.meta["job_id"] = getattr(job, "id", None)
        self.store.save(cp)
        self.audit.record(workflow_id=wf.id, event="workflow_created", state=cp.state.value,
                          detail={"steps": len(ordered)})
        return cp

    def run(self, workflow_id: str) -> WorkflowCheckpoint:
        cp = self._load(workflow_id)
        if cp.state.is_terminal:
            return cp
        return self._drive(cp)

    def resume(self, workflow_id: str) -> WorkflowCheckpoint:
        cp = self._load(workflow_id)
        if cp.state.is_terminal:
            return cp
        if cp.state == WorkflowState.ROLLBACK_READY:
            return cp
        if cp.state == WorkflowState.WAITING_APPROVAL:
            return self._resume_after_approval(cp)
        # PENDING / RUNNING / RETRYING -> continue (also the crash case)
        return self._drive(cp)

    def resume_after_approval(self, workflow_id: str) -> WorkflowCheckpoint:
        cp = self._load(workflow_id)
        if cp.state != WorkflowState.WAITING_APPROVAL:
            return cp
        return self._resume_after_approval(cp)

    def resume_after_crash(self, workflow_id: str) -> WorkflowCheckpoint:
        cp = self._load(workflow_id)
        if cp.state.is_terminal or cp.state == WorkflowState.WAITING_APPROVAL:
            return cp
        # A step left in "running" means the process died mid-step: reset it so
        # it is retried cleanly from the last durable checkpoint.
        runs = cp.step_runs
        for sid, raw in runs.items():
            if raw.get("status") == STEP_RUNNING:
                raw["status"] = STEP_PENDING
        self.audit.record(workflow_id=cp.workflow_id, event="resume_after_crash", state=cp.state.value)
        return self._drive(cp)

    def cancel(self, workflow_id: str) -> WorkflowCheckpoint:
        cp = self._load(workflow_id)
        if cp.state.is_terminal:
            return cp
        cp.state = WorkflowState.CANCELLED
        self._sync_job(cp, "cancelled")
        self._notify(cp, "Workflow abgebrochen", cp.objective, level="warning")
        self._commit(cp, event="workflow_cancelled")
        return cp

    def prepare_rollback(self, workflow_id: str) -> dict[str, Any]:
        """Compute (do NOT execute) the reverse plan for completed steps."""

        cp = self._load(workflow_id)
        runs = cp.runs()
        completed = [s for s in cp.steps if runs.get(s["id"], StepRun(s["id"])).status == STEP_COMPLETED]
        plan = [
            {"step_id": s["id"], "name": s.get("name"), "tool_name": s.get("tool_name"),
             "output": runs[s["id"]].output}
            for s in reversed(completed)
        ]
        if not cp.state.is_terminal:
            cp.state = WorkflowState.ROLLBACK_READY
            self._commit(cp, event="rollback_prepared", detail={"steps": len(plan)})
        else:
            self.audit.record(workflow_id=cp.workflow_id, event="rollback_prepared",
                              state=cp.state.value, detail={"steps": len(plan)})
        return {"workflow_id": cp.workflow_id, "state": cp.state.value, "rollback": plan}

    def status(self, workflow_id: str) -> dict[str, Any]:
        cp = self._load(workflow_id)
        runs = cp.runs()
        done = sum(1 for r in runs.values() if r.status == STEP_COMPLETED)
        return {
            "workflow_id": cp.workflow_id,
            "objective": cp.objective,
            "state": cp.state.value,
            "cursor": cp.cursor,
            "steps_total": len(cp.steps),
            "steps_completed": done,
            "error": cp.error,
            "job_id": cp.meta.get("job_id"),
            "step_runs": cp.step_runs,
            "updated_at": cp.updated_at,
        }

    def list(self) -> list[dict[str, Any]]:
        return [
            {"workflow_id": cp.workflow_id, "objective": cp.objective, "state": cp.state.value,
             "steps_total": len(cp.steps)}
            for cp in self.store.list()
        ]

    def audit_events(self, workflow_id: str | None = None, *, limit: int = 200) -> list[dict[str, Any]]:
        return self.audit.events(workflow_id, limit=limit)

    # -- core loop ---------------------------------------------------------
    def _drive(self, cp: WorkflowCheckpoint) -> WorkflowCheckpoint:
        steps = [WorkflowStep(**_coerce_step(s)) for s in cp.steps]
        runs = cp.runs()
        cp.state = WorkflowState.RUNNING
        self._sync_job(cp, "running")
        self._commit(cp, event="workflow_running")

        while cp.cursor < len(steps):
            step = steps[cp.cursor]
            run = runs[step.id]

            if run.status == STEP_COMPLETED:
                cp.cursor += 1
                continue

            missing = [d for d in step.dependencies if runs.get(d, StepRun(d)).status != STEP_COMPLETED]
            if missing:
                return self._fail(cp, runs, step, f"dependency_not_completed:{','.join(missing)}")

            approval_required, blocked = self._approval_requirement(step)
            if blocked:
                return self._fail(cp, runs, step, "policy_blocked")

            if approval_required:
                decision = self._check_approval(cp, step, run)
                if decision in {"pending", "deferred"}:
                    return self._wait_for_approval(cp, runs, step, run)
                if decision == "rejected":
                    return self._fail(cp, runs, step, "approval_rejected")
                # approved -> fall through and execute

            verdict = self._execute_step(cp, step, run, approved=approval_required)
            self._persist_runs(cp, runs)

            if run.status == STEP_COMPLETED:
                cp.cursor += 1
                self._commit(cp, event="step_completed", step_id=step.id)
                continue

            # step did not complete -> map recovery verdict to workflow state
            if verdict is not None and verdict.strategy == WAIT_FOR_APPROVAL:
                return self._wait_for_approval(cp, runs, step, run)
            if verdict is not None and verdict.strategy == ROLLBACK:
                return self._rollback_ready(cp, runs, step, run)
            return self._fail(cp, runs, step, run.error or "step_failed")

        return self._complete(cp, runs)

    def _execute_step(self, cp: WorkflowCheckpoint, step: WorkflowStep, run: StepRun, *, approved: bool):
        run.status = STEP_RUNNING
        run.started_at = run.started_at or _now()
        self.audit.record(workflow_id=cp.workflow_id, event="step_started", step_id=step.id, state=cp.state.value)

        while True:
            run.attempts += 1
            try:
                output = self._run_tool(step, approved)
                run.output = output
                run.status = STEP_COMPLETED
                run.ended_at = _now()
                run.error = ""
                self.audit.record(workflow_id=cp.workflow_id, event="step_completed", step_id=step.id,
                                  detail={"attempts": run.attempts})
                self._remember({"kind": "workflow_step", "workflow_id": cp.workflow_id,
                                "step_id": step.id, "output": output})
                return None
            except Exception as exc:  # noqa: BLE001 - recovery classifies below
                verdict = self.recovery.decide(exc, attempt=run.attempts, max_retries=step.max_retries)
                run.error = str(exc)
                self.audit.record(workflow_id=cp.workflow_id, event="step_error", step_id=step.id,
                                  detail={"attempt": run.attempts, "error": str(exc), "verdict": verdict.to_dict()})
                if verdict.should_retry:
                    continue
                if verdict.strategy == WAIT_FOR_APPROVAL:
                    run.status = STEP_WAITING_APPROVAL
                else:
                    run.status = STEP_FAILED
                    run.ended_at = _now()
                return verdict

    def _run_tool(self, step: WorkflowStep, approved: bool) -> Any:
        if step.tool_name is None:
            return None  # manual / checkpoint step: no-op success
        if self._tool_runner is not None:
            return self._tool_runner(step, approved)
        if self.tool_registry is None:
            raise RuntimeError(f"no_tool_runtime_for:{step.tool_name}")
        result = self.tool_registry.run(step.tool_name, step.input, approved=approved)
        if getattr(result, "success", False):
            return getattr(result, "output", None)
        raise RuntimeError(getattr(result, "error", None) or f"tool_failed:{step.tool_name}")

    # -- approval integration (reuses v30.61 SafetyService) ---------------
    def _approval_requirement(self, step: WorkflowStep) -> tuple[bool, bool]:
        """Return (requires_approval, blocked_by_policy)."""

        if step.requires_approval:
            return True, False
        if self.safety is None:
            return False, False
        risk_level, verdict = self.safety.policy_check(step.tool_name or step.name)
        _ = risk_level
        if verdict.outcome == "block":
            return False, True
        return bool(verdict.requires_approval), False

    def _category_for_step(self, step: WorkflowStep) -> str:
        action = (step.tool_name or step.name or "").lower()
        if "delete" in action:
            return "delete_request"
        if "permission" in action or "role" in action:
            return "connector_permission_change"
        return "risky_agent_action"

    def _check_approval(self, cp: WorkflowCheckpoint, step: WorkflowStep, run: StepRun) -> str:
        if self.safety is None:
            raise RuntimeError("approval_layer_unavailable")
        target = f"{cp.workflow_id}:{step.id}"
        record = self.safety.get(run.approval_id) if run.approval_id else None
        if record is None:
            record = self.safety.request(
                actor=self.actor,
                action=step.tool_name or step.name,
                intent=step.name,
                text=cp.objective,
                target=target,
                category=self._category_for_step(step),
            )
            run.approval_id = record["approval_id"]
        return record.get("status", "pending")

    def _wait_for_approval(self, cp, runs, step, run) -> WorkflowCheckpoint:
        run.status = STEP_WAITING_APPROVAL
        cp.state = WorkflowState.WAITING_APPROVAL
        self._persist_runs(cp, runs)
        self._sync_job(cp, "blocked")
        self._notify(cp, "Freigabe erforderlich", f"{step.name} wartet auf Freigabe",
                     level="action_required", action_required=True,
                     metadata={"approval_id": run.approval_id, "step_id": step.id})
        self._commit(cp, event="waiting_approval", step_id=step.id,
                     detail={"approval_id": run.approval_id})
        return cp

    def _resume_after_approval(self, cp: WorkflowCheckpoint) -> WorkflowCheckpoint:
        steps = [WorkflowStep(**_coerce_step(s)) for s in cp.steps]
        runs = cp.runs()
        if cp.cursor >= len(steps):
            return self._complete(cp, runs)
        step = steps[cp.cursor]
        run = runs[step.id]
        status = self._check_approval(cp, step, run)
        if status == "approved":
            self.audit.record(workflow_id=cp.workflow_id, event="approval_granted", step_id=step.id)
            self._persist_runs(cp, runs)
            return self._drive(cp)
        if status == "rejected":
            return self._fail(cp, runs, step, "approval_rejected")
        # still pending/deferred
        self.audit.record(workflow_id=cp.workflow_id, event="approval_still_pending", step_id=step.id,
                          detail={"status": status})
        return cp

    # -- terminal transitions ---------------------------------------------
    def _complete(self, cp, runs) -> WorkflowCheckpoint:
        cp.state = WorkflowState.COMPLETED
        self._persist_runs(cp, runs)
        self._sync_job(cp, "success")
        self._notify(cp, "Workflow abgeschlossen", cp.objective, level="success")
        self._remember({"kind": "workflow_completed", "workflow_id": cp.workflow_id, "objective": cp.objective})
        self._commit(cp, event="workflow_completed")
        return cp

    def _fail(self, cp, runs, step, error: str) -> WorkflowCheckpoint:
        cp.state = WorkflowState.FAILED
        cp.error = error
        if step is not None:
            run = runs.get(step.id)
            if run is not None:
                run.status = STEP_FAILED
                run.error = error
        self._persist_runs(cp, runs)
        self._sync_job(cp, "failed", error=error)
        self._notify(cp, "Workflow fehlgeschlagen", f"{cp.objective}: {error}", level="error")
        self._remember({"kind": "workflow_failed", "workflow_id": cp.workflow_id, "error": error})
        self._commit(cp, event="workflow_failed", step_id=getattr(step, "id", ""), detail={"error": error})
        return cp

    def _rollback_ready(self, cp, runs, step, run) -> WorkflowCheckpoint:
        cp.state = WorkflowState.ROLLBACK_READY
        cp.error = run.error or "rollback_required"
        self._persist_runs(cp, runs)
        self._sync_job(cp, "failed", error=cp.error)
        self._notify(cp, "Rollback vorbereitet", f"{cp.objective}: {cp.error}", level="error",
                     metadata={"step_id": step.id})
        self._commit(cp, event="rollback_ready", step_id=step.id, detail={"error": cp.error})
        return cp

    # -- helpers -----------------------------------------------------------
    def _load(self, workflow_id: str) -> WorkflowCheckpoint:
        cp = self.store.load(workflow_id)
        if cp is None:
            raise KeyError(f"unknown_workflow:{workflow_id}")
        return cp

    def _persist_runs(self, cp: WorkflowCheckpoint, runs: dict[str, StepRun]) -> None:
        cp.step_runs = {sid: r.to_dict() for sid, r in runs.items()}

    def _commit(self, cp: WorkflowCheckpoint, *, event: str, step_id: str = "", detail: dict | None = None) -> None:
        cp.updated_at = _now()
        self.store.save(cp)
        self.audit.record(workflow_id=cp.workflow_id, event=event, state=cp.state.value,
                          step_id=step_id, detail=detail or {})

    def _sync_job(self, cp: WorkflowCheckpoint, status: str, *, error: str | None = None) -> None:
        if self.jobs is None:
            return
        job_id = cp.meta.get("job_id")
        if not job_id:
            return
        try:
            self.jobs.update_status(job_id, status, error=error)
        except Exception:
            pass

    def _notify(self, cp: WorkflowCheckpoint, title: str, message: str, *, level: str = "info",
                action_required: bool = False, metadata: dict | None = None) -> None:
        if self.notifications is None:
            return
        try:
            self.notifications.notify(title, message, level=level, category="agent",
                                      source="workflow", action_required=action_required,
                                      metadata={"workflow_id": cp.workflow_id, **(metadata or {})})
        except Exception:
            pass

    def _remember(self, fact: dict[str, Any]) -> None:
        if self.memory_sink is None:
            return
        try:
            self.memory_sink(fact)
        except Exception:
            pass


def _coerce_step(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": data["id"],
        "name": data.get("name", data["id"]),
        "tool_name": data.get("tool_name"),
        "input": dict(data.get("input", {})),
        "dependencies": list(data.get("dependencies", [])),
        "timeout_seconds": int(data.get("timeout_seconds", 300)),
        "max_retries": int(data.get("max_retries", 3)),
        "requires_approval": bool(data.get("requires_approval", False)),
    }
