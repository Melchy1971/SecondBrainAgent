from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class JobState(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

    @property
    def terminal(self) -> bool:
        return self in {self.COMPLETED, self.FAILED, self.CANCELLED, self.TIMEOUT}


TERMINAL_STATES = {JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED, JobState.TIMEOUT}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(slots=True)
class DesktopJob:
    name: str
    job_id: str = field(default_factory=lambda: str(uuid4()))
    state: JobState = JobState.CREATED
    progress: int = 0
    created_at: str = field(default_factory=utc_now_iso)
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def mark_queued(self) -> None:
        if self.state.terminal:
            raise ValueError("terminal job cannot be queued")
        self.state = JobState.QUEUED

    def mark_running(self) -> None:
        if self.state.terminal:
            raise ValueError("terminal job cannot be started")
        self.state = JobState.RUNNING
        self.started_at = self.started_at or utc_now_iso()

    def mark_progress(self, progress: int) -> None:
        if self.state.terminal:
            raise ValueError("terminal job progress cannot change")
        self.progress = max(0, min(100, int(progress)))

    def mark_completed(self) -> None:
        self.progress = 100
        self.state = JobState.COMPLETED
        self.finished_at = utc_now_iso()
        self.error = None

    def mark_failed(self, error: str) -> None:
        self.state = JobState.FAILED
        self.finished_at = utc_now_iso()
        self.error = error or "unknown error"

    def mark_cancelled(self) -> None:
        self.state = JobState.CANCELLED
        self.finished_at = utc_now_iso()

    def mark_timeout(self, error: str = "job timeout") -> None:
        self.state = JobState.TIMEOUT
        self.finished_at = utc_now_iso()
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["state"] = self.state.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DesktopJob":
        payload = dict(data)
        payload["state"] = JobState(payload.get("state", JobState.CREATED.value))
        return cls(**payload)
