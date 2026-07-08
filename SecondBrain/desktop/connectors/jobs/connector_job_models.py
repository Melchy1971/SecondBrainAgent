from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class ConnectorJobState(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConnectorJobType(str, Enum):
    SYNC = "sync"
    HEALTH_CHECK = "health_check"
    CONFIG_VALIDATE = "config_validate"


@dataclass(frozen=True)
class ConnectorJob:
    job_id: str
    connector_id: str
    job_type: ConnectorJobType = ConnectorJobType.SYNC
    state: ConnectorJobState = ConnectorJobState.CREATED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    finished_at: datetime | None = None
    cursor_before: str | None = None
    cursor_after: str | None = None
    items_processed: int = 0
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, connector_id: str, *, job_type: ConnectorJobType = ConnectorJobType.SYNC, cursor_before: str | None = None, metadata: dict[str, Any] | None = None) -> "ConnectorJob":
        if not connector_id or not connector_id.strip():
            raise ValueError("connector_id is required")
        return cls(
            job_id=f"connector-job-{uuid4().hex[:12]}",
            connector_id=connector_id.strip(),
            job_type=job_type,
            cursor_before=cursor_before,
            metadata=dict(metadata or {}),
        )

    def queued(self) -> "ConnectorJob":
        return replace(self, state=ConnectorJobState.QUEUED)

    def running(self) -> "ConnectorJob":
        return replace(self, state=ConnectorJobState.RUNNING, started_at=datetime.now(timezone.utc), error=None)

    def completed(self, *, items_processed: int = 0, cursor_after: str | None = None) -> "ConnectorJob":
        return replace(
            self,
            state=ConnectorJobState.COMPLETED,
            finished_at=datetime.now(timezone.utc),
            items_processed=max(0, items_processed),
            cursor_after=cursor_after,
            error=None,
        )

    def failed(self, error: str) -> "ConnectorJob":
        return replace(
            self,
            state=ConnectorJobState.FAILED,
            finished_at=datetime.now(timezone.utc),
            error=error or "unknown connector job error",
        )

    def cancelled(self, reason: str = "cancelled") -> "ConnectorJob":
        return replace(self, state=ConnectorJobState.CANCELLED, finished_at=datetime.now(timezone.utc), error=reason)

    @property
    def terminal(self) -> bool:
        return self.state in {ConnectorJobState.COMPLETED, ConnectorJobState.FAILED, ConnectorJobState.CANCELLED}

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "connector_id": self.connector_id,
            "job_type": self.job_type.value,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "cursor_before": self.cursor_before,
            "cursor_after": self.cursor_after,
            "items_processed": self.items_processed,
            "error": self.error,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ConnectorJobResult:
    job: ConnectorJob
    accepted: bool
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"accepted": self.accepted, "message": self.message, "job": self.job.to_dict()}
