"""v30.71 Scheduler - RecurringJob and JobRun models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


@dataclass
class RecurringJob:
    id: str
    name: str
    schedule: dict[str, Any]           # {"cron": "..."} or {"interval_seconds": n}
    kind: str = "system"               # JobQueue kind to enqueue
    payload: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)  # ids that must run first
    enabled: bool = True
    last_run_at: str | None = None
    last_status: str | None = None
    run_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RecurringJob":
        return cls(
            id=data["id"], name=data.get("name", data["id"]),
            schedule=dict(data.get("schedule", {})), kind=data.get("kind", "system"),
            payload=dict(data.get("payload", {})), dependencies=list(data.get("dependencies", [])),
            enabled=bool(data.get("enabled", True)), last_run_at=data.get("last_run_at"),
            last_status=data.get("last_status"), run_count=int(data.get("run_count", 0)),
        )

    @classmethod
    def create(cls, name: str, schedule: dict | str, *, kind: str = "system",
               payload: dict | None = None, dependencies: list[str] | None = None,
               job_id: str | None = None, enabled: bool = True) -> "RecurringJob":
        sched = {"cron": schedule} if isinstance(schedule, str) else dict(schedule)
        return cls(id=job_id or new_id("rjob"), name=name, schedule=sched, kind=kind,
                   payload=payload or {}, dependencies=list(dependencies or []), enabled=enabled)


@dataclass
class JobRun:
    run_id: str
    job_id: str
    name: str
    status: str                        # success | failed | skipped
    started_at: str
    ended_at: str = ""
    output: Any = None
    error: str = ""
    queue_job_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JobRun":
        return cls(
            run_id=data["run_id"], job_id=data["job_id"], name=data.get("name", ""),
            status=data.get("status", "skipped"), started_at=data.get("started_at", ""),
            ended_at=data.get("ended_at", ""), output=data.get("output"),
            error=data.get("error", ""), queue_job_id=data.get("queue_job_id", ""),
        )
