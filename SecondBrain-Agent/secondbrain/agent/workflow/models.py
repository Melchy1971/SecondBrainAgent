"""v30.62 Agent Workflow Engine - domain models.

The runtime step definition (:class:`WorkflowStep`) and status enum
(:class:`WorkflowStatus`) are reused from ``secondbrain.agent.workflow_models``
so the engine does not fork the existing step schema. On top of that this module
adds the *runtime* aggregate (``Workflow``), the live per-run state
(``WorkflowState`` + ``StepRun``) and the serializable ``WorkflowCheckpoint``
used for crash recovery.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

# Reuse the existing step + status contract (do not redefine).
from secondbrain.agent.workflow_models import WorkflowStatus, WorkflowStep  # noqa: F401

CHECKPOINT_SCHEMA = "secondbrain.agent.workflow.checkpoint.v30_62"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class WorkflowState(str, Enum):
    """Lifecycle state of a workflow run.

    Superset of :class:`WorkflowStatus`: every ``WorkflowStatus`` value maps 1:1,
    with the extra runtime states the engine needs (``RETRYING``,
    ``ROLLBACK_READY``).
    """

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    RETRYING = "RETRYING"
    ROLLBACK_READY = "ROLLBACK_READY"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

    @property
    def is_terminal(self) -> bool:
        return self in {WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED}

    @property
    def is_resumable(self) -> bool:
        return self in {
            WorkflowState.PENDING,
            WorkflowState.RUNNING,
            WorkflowState.RETRYING,
            WorkflowState.WAITING_APPROVAL,
            WorkflowState.ROLLBACK_READY,
        }


# Per-step runtime status values.
STEP_PENDING = "pending"
STEP_RUNNING = "running"
STEP_WAITING_APPROVAL = "waiting_approval"
STEP_COMPLETED = "completed"
STEP_FAILED = "failed"
STEP_SKIPPED = "skipped"


@dataclass
class StepRun:
    """Mutable execution record for a single step within one workflow run."""

    step_id: str
    status: str = STEP_PENDING
    attempts: int = 0
    output: Any = None
    error: str = ""
    approval_id: str = ""
    started_at: str = ""
    ended_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StepRun":
        return cls(
            step_id=data["step_id"],
            status=data.get("status", STEP_PENDING),
            attempts=int(data.get("attempts", 0)),
            output=data.get("output"),
            error=data.get("error", ""),
            approval_id=data.get("approval_id", ""),
            started_at=data.get("started_at", ""),
            ended_at=data.get("ended_at", ""),
        )


@dataclass
class Workflow:
    """A multi-step agent plan made executable."""

    id: str
    objective: str
    steps: list[WorkflowStep] = field(default_factory=list)

    def step(self, step_id: str) -> WorkflowStep | None:
        for s in self.steps:
            if s.id == step_id:
                return s
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "objective": self.objective,
            "steps": [_step_to_dict(s) for s in self.steps],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Workflow":
        return cls(
            id=data["id"],
            objective=data.get("objective", ""),
            steps=[_step_from_dict(s) for s in data.get("steps", [])],
        )


def _step_to_dict(step: WorkflowStep) -> dict[str, Any]:
    return {
        "id": step.id,
        "name": step.name,
        "tool_name": step.tool_name,
        "input": dict(step.input),
        "dependencies": list(step.dependencies),
        "timeout_seconds": step.timeout_seconds,
        "max_retries": step.max_retries,
        "requires_approval": step.requires_approval,
    }


def _step_from_dict(data: dict[str, Any]) -> WorkflowStep:
    return WorkflowStep(
        id=data["id"],
        name=data.get("name", data["id"]),
        tool_name=data.get("tool_name"),
        input=dict(data.get("input", {})),
        dependencies=list(data.get("dependencies", [])),
        timeout_seconds=int(data.get("timeout_seconds", 300)),
        max_retries=int(data.get("max_retries", 3)),
        requires_approval=bool(data.get("requires_approval", False)),
    )


@dataclass
class WorkflowCheckpoint:
    """Serializable snapshot of a workflow run - the crash-recovery unit."""

    workflow_id: str
    objective: str
    state: WorkflowState
    cursor: int
    steps: list[dict[str, Any]]
    step_runs: dict[str, dict[str, Any]]
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    error: str = ""
    meta: dict[str, Any] = field(default_factory=dict)
    schema: str = CHECKPOINT_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["state"] = self.state.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowCheckpoint":
        return cls(
            workflow_id=data["workflow_id"],
            objective=data.get("objective", ""),
            state=WorkflowState(data.get("state", "PENDING")),
            cursor=int(data.get("cursor", 0)),
            steps=list(data.get("steps", [])),
            step_runs=dict(data.get("step_runs", {})),
            created_at=data.get("created_at", utc_now()),
            updated_at=data.get("updated_at", utc_now()),
            error=data.get("error", ""),
            meta=dict(data.get("meta", {})),
            schema=data.get("schema", CHECKPOINT_SCHEMA),
        )

    def workflow(self) -> Workflow:
        return Workflow.from_dict({"id": self.workflow_id, "objective": self.objective, "steps": self.steps})

    def runs(self) -> dict[str, StepRun]:
        return {sid: StepRun.from_dict(raw) for sid, raw in self.step_runs.items()}
