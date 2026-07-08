from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class AgentJobStatus(str, Enum):
    CREATED = 'created'
    QUEUED = 'queued'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    RETRYING = 'retrying'


@dataclass(slots=True)
class AgentJobResult:
    success: bool
    output: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AgentJob:
    title: str
    plan_id: str
    job_id: str = field(default_factory=lambda: str(uuid4()))
    status: AgentJobStatus = AgentJobStatus.CREATED
    progress: int = 0
    attempt: int = 0
    max_attempts: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
    result: AgentJobResult | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def mark_queued(self) -> None:
        self.status = AgentJobStatus.QUEUED

    def mark_running(self) -> None:
        self.status = AgentJobStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
        self.attempt += 1

    def update_progress(self, progress: int) -> None:
        self.progress = max(0, min(100, int(progress)))

    def mark_completed(self, result: AgentJobResult | None = None) -> None:
        self.status = AgentJobStatus.COMPLETED
        self.progress = 100
        self.finished_at = datetime.now(timezone.utc)
        self.error = None
        self.result = result or AgentJobResult(success=True)

    def mark_failed(self, error: str) -> None:
        self.status = AgentJobStatus.FAILED
        self.finished_at = datetime.now(timezone.utc)
        self.error = error
        self.result = AgentJobResult(success=False, error=error)

    def mark_cancelled(self, reason: str = 'cancelled') -> None:
        self.status = AgentJobStatus.CANCELLED
        self.finished_at = datetime.now(timezone.utc)
        self.error = reason
        self.result = AgentJobResult(success=False, error=reason)

    def can_retry(self) -> bool:
        return self.attempt < self.max_attempts and self.status == AgentJobStatus.FAILED
