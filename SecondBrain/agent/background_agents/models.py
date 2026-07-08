"""v30.63 Background Agents - domain models.

A ``BackgroundAgent`` is a registered, long-running or recurring task Jarvis runs
on its own: a monitor or a periodic maintenance job. Each execution is one
``AgentRun`` (driven through the v30.62 Workflow Engine), liveness is tracked by
``AgentHeartbeat``, and repeated failures are governed by ``AgentFailurePolicy``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_ts(value: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


class AgentState(str, Enum):
    REGISTERED = "REGISTERED"
    ACTIVE = "ACTIVE"        # started, eligible to run on schedule
    PAUSED = "PAUSED"        # temporarily suspended, keeps its schedule
    STOPPED = "STOPPED"      # not running, will not be scheduled
    FAILED = "FAILED"        # disabled by the failure policy

    @property
    def is_runnable(self) -> bool:
        return self == AgentState.ACTIVE


class AgentType(str, Enum):
    IMPORT_MONITOR = "import_monitor"
    KNOWLEDGE_QUALITY_MONITOR = "knowledge_quality_monitor"
    MEMORY_CONSOLIDATION = "memory_consolidation"
    RAG_INDEX_MONITOR = "rag_index_monitor"
    NOTIFICATION_AGENT = "notification_agent"
    SYSTEM_HEALTH_AGENT = "system_health_agent"

    @classmethod
    def parse(cls, value: "AgentType | str") -> "AgentType":
        if isinstance(value, AgentType):
            return value
        return cls(str(value).strip().lower())


RUN_SUCCESS = "success"
RUN_FAILED = "failed"
RUN_SKIPPED = "skipped"


@dataclass
class AgentSchedule:
    """When an agent is due. Interval-based; ``interval_seconds <= 0`` means the
    agent only runs on explicit demand (manual trigger)."""

    interval_seconds: int = 0
    jitter_seconds: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {"interval_seconds": self.interval_seconds, "jitter_seconds": self.jitter_seconds}

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "AgentSchedule":
        data = data or {}
        return cls(
            interval_seconds=int(data.get("interval_seconds", 0)),
            jitter_seconds=int(data.get("jitter_seconds", 0)),
        )

    @property
    def is_manual(self) -> bool:
        return self.interval_seconds <= 0

    def is_due(self, *, last_run: str | None, now: datetime | None = None) -> bool:
        if self.is_manual:
            return False
        if not last_run:
            return True
        current = now or datetime.now(timezone.utc)
        last = _parse_ts(last_run)
        if last is None:
            return True
        return (current - last).total_seconds() >= self.interval_seconds

    def next_due(self, *, last_run: str | None) -> str | None:
        if self.is_manual or not last_run:
            return None
        last = _parse_ts(last_run)
        if last is None:
            return None
        from datetime import timedelta

        return (last + timedelta(seconds=self.interval_seconds)).isoformat(timespec="seconds")


@dataclass
class AgentFailurePolicy:
    """Governs what happens after repeated failures."""

    max_consecutive_failures: int = 3
    action: str = "pause"   # "pause" | "stop" | "alert_only"
    notify: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "AgentFailurePolicy":
        data = data or {}
        return cls(
            max_consecutive_failures=int(data.get("max_consecutive_failures", 3)),
            action=str(data.get("action", "pause")),
            notify=bool(data.get("notify", True)),
        )

    def tripped(self, consecutive_failures: int) -> bool:
        return consecutive_failures >= self.max_consecutive_failures


@dataclass
class BackgroundAgent:
    id: str
    name: str
    agent_type: AgentType
    schedule: AgentSchedule = field(default_factory=AgentSchedule)
    failure_policy: AgentFailurePolicy = field(default_factory=AgentFailurePolicy)
    state: AgentState = AgentState.REGISTERED
    config: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    last_run_at: str | None = None
    last_status: str | None = None
    consecutive_failures: int = 0
    total_runs: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "agent_type": self.agent_type.value,
            "schedule": self.schedule.to_dict(),
            "failure_policy": self.failure_policy.to_dict(),
            "state": self.state.value,
            "config": self.config,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_run_at": self.last_run_at,
            "last_status": self.last_status,
            "consecutive_failures": self.consecutive_failures,
            "total_runs": self.total_runs,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BackgroundAgent":
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            agent_type=AgentType.parse(data["agent_type"]),
            schedule=AgentSchedule.from_dict(data.get("schedule")),
            failure_policy=AgentFailurePolicy.from_dict(data.get("failure_policy")),
            state=AgentState(data.get("state", "REGISTERED")),
            config=dict(data.get("config", {})),
            created_at=data.get("created_at", utc_now()),
            updated_at=data.get("updated_at", utc_now()),
            last_run_at=data.get("last_run_at"),
            last_status=data.get("last_status"),
            consecutive_failures=int(data.get("consecutive_failures", 0)),
            total_runs=int(data.get("total_runs", 0)),
        )


@dataclass
class AgentRun:
    run_id: str
    agent_id: str
    agent_type: str
    status: str
    started_at: str
    ended_at: str = ""
    output: Any = None
    error: str = ""
    workflow_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentRun":
        return cls(
            run_id=data["run_id"],
            agent_id=data["agent_id"],
            agent_type=data.get("agent_type", ""),
            status=data.get("status", RUN_SKIPPED),
            started_at=data.get("started_at", ""),
            ended_at=data.get("ended_at", ""),
            output=data.get("output"),
            error=data.get("error", ""),
            workflow_id=data.get("workflow_id", ""),
        )


@dataclass
class AgentHeartbeat:
    agent_id: str
    ts: str
    state: str
    sequence: int = 0
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentHeartbeat":
        return cls(
            agent_id=data["agent_id"],
            ts=data.get("ts", ""),
            state=data.get("state", ""),
            sequence=int(data.get("sequence", 0)),
            detail=dict(data.get("detail", {})),
        )

    def is_stale(self, *, ttl_seconds: int, now: datetime | None = None) -> bool:
        current = now or datetime.now(timezone.utc)
        ts = _parse_ts(self.ts)
        if ts is None:
            return True
        return (current - ts).total_seconds() >= ttl_seconds
