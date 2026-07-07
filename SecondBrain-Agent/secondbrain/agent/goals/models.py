"""v30.65 Agent Goal Tracking - domain models.

A ``Goal`` bundles milestones, metrics, evidence and links to decomposed plans.
Progress is computed deterministically from milestones, metrics and (via the
tracker) linked plans/workflows.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


class GoalStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    AT_RISK = "AT_RISK"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

    @property
    def is_terminal(self) -> bool:
        return self in {GoalStatus.COMPLETED, GoalStatus.CANCELLED}


@dataclass
class GoalMetric:
    name: str
    target: float
    current: float = 0.0
    baseline: float = 0.0
    unit: str = ""
    direction: str = "increase"  # "increase" | "decrease"

    def progress(self) -> float:
        b, c, t = self.baseline, self.current, self.target
        if self.direction == "decrease":
            if b == t:
                return 1.0 if c <= t else 0.0
            return _clamp((b - c) / (b - t))
        if t == b:
            return 1.0 if c >= t else 0.0
        return _clamp((c - b) / (t - b))

    @property
    def reached(self) -> bool:
        return self.progress() >= 1.0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["progress"] = round(self.progress(), 4)
        data["reached"] = self.reached
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GoalMetric":
        return cls(
            name=data["name"],
            target=float(data.get("target", 0.0)),
            current=float(data.get("current", 0.0)),
            baseline=float(data.get("baseline", 0.0)),
            unit=data.get("unit", ""),
            direction=data.get("direction", "increase"),
        )


@dataclass
class GoalMilestone:
    id: str
    title: str
    done: bool = False
    weight: float = 1.0
    due: str | None = None
    plan_id: str = ""
    workflow_id: str = ""

    def is_overdue(self, now: datetime | None = None) -> bool:
        if self.done:
            return False
        due = _parse_ts(self.due)
        if due is None:
            return False
        return (now or datetime.now(timezone.utc)) > due

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GoalMilestone":
        return cls(
            id=data["id"],
            title=data.get("title", data["id"]),
            done=bool(data.get("done", False)),
            weight=float(data.get("weight", 1.0)),
            due=data.get("due"),
            plan_id=data.get("plan_id", ""),
            workflow_id=data.get("workflow_id", ""),
        )


@dataclass
class GoalEvidence:
    id: str
    ts: str
    source: str
    note: str = ""
    ref: str = ""  # e.g. "plan:<id>" / "workflow:<id>" / "memory:<id>"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GoalEvidence":
        return cls(id=data["id"], ts=data.get("ts", ""), source=data.get("source", ""),
                   note=data.get("note", ""), ref=data.get("ref", ""))


@dataclass
class GoalReview:
    id: str
    goal_id: str
    ts: str
    progress: float
    status: str
    risks: list[str] = field(default_factory=list)
    summary: str = ""
    metrics: list[dict[str, Any]] = field(default_factory=list)
    milestones: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GoalReview":
        return cls(
            id=data["id"], goal_id=data["goal_id"], ts=data.get("ts", ""),
            progress=float(data.get("progress", 0.0)), status=data.get("status", ""),
            risks=list(data.get("risks", [])), summary=data.get("summary", ""),
            metrics=list(data.get("metrics", [])), milestones=list(data.get("milestones", [])),
        )


@dataclass
class Goal:
    id: str
    title: str
    description: str = ""
    status: GoalStatus = GoalStatus.DRAFT
    workspace_id: str | None = None
    owner: str = ""
    target_date: str | None = None
    milestones: list[GoalMilestone] = field(default_factory=list)
    metrics: list[GoalMetric] = field(default_factory=list)
    plan_ids: list[str] = field(default_factory=list)
    evidence: list[GoalEvidence] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    # -- progress components ----------------------------------------------
    def milestone_progress(self) -> float | None:
        if not self.milestones:
            return None
        total = sum(max(0.0, m.weight) for m in self.milestones) or float(len(self.milestones))
        done = sum(max(0.0, m.weight) for m in self.milestones if m.done)
        return _clamp(done / total) if total else 0.0

    def metric_progress(self) -> float | None:
        if not self.metrics:
            return None
        return _clamp(sum(m.progress() for m in self.metrics) / len(self.metrics))

    def milestone(self, milestone_id: str) -> GoalMilestone | None:
        for m in self.milestones:
            if m.id == milestone_id:
                return m
        return None

    def metric(self, name: str) -> GoalMetric | None:
        for m in self.metrics:
            if m.name == name:
                return m
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "workspace_id": self.workspace_id,
            "owner": self.owner,
            "target_date": self.target_date,
            "milestones": [m.to_dict() for m in self.milestones],
            "metrics": [m.to_dict() for m in self.metrics],
            "plan_ids": list(self.plan_ids),
            "evidence": [e.to_dict() for e in self.evidence],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Goal":
        return cls(
            id=data["id"],
            title=data.get("title", data["id"]),
            description=data.get("description", ""),
            status=GoalStatus(data.get("status", "DRAFT")),
            workspace_id=data.get("workspace_id"),
            owner=data.get("owner", ""),
            target_date=data.get("target_date"),
            milestones=[GoalMilestone.from_dict(m) for m in data.get("milestones", [])],
            metrics=[GoalMetric.from_dict(m) for m in data.get("metrics", [])],
            plan_ids=list(data.get("plan_ids", [])),
            evidence=[GoalEvidence.from_dict(e) for e in data.get("evidence", [])],
            created_at=data.get("created_at", utc_now()),
            updated_at=data.get("updated_at", utc_now()),
            metadata=dict(data.get("metadata", {})),
        )


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"
