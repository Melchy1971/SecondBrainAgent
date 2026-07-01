from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

JobStatus = Literal["pending", "running", "success", "failed", "cancelled", "blocked"]
JobKind = Literal["import", "reindex", "agent", "voice", "update", "approval", "system"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class QueueJob:
    id: str
    kind: JobKind
    title: str
    status: JobStatus = "pending"
    priority: int = 50
    created_at: str = ""
    updated_at: str = ""
    payload: dict[str, Any] | None = None
    error: str | None = None
    approval_required: bool = False

    @staticmethod
    def create(kind: JobKind, title: str, *, priority: int = 50, payload: dict[str, Any] | None = None, approval_required: bool = False) -> "QueueJob":
        now = utc_now()
        status: JobStatus = "blocked" if approval_required else "pending"
        return QueueJob(
            id=f"job_{uuid4().hex[:12]}",
            kind=kind,
            title=title,
            status=status,
            priority=priority,
            created_at=now,
            updated_at=now,
            payload=payload or {},
            approval_required=approval_required,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "QueueJob":
        return QueueJob(
            id=str(data["id"]),
            kind=data.get("kind", "system"),
            title=str(data.get("title", "Unbenannter Job")),
            status=data.get("status", "pending"),
            priority=int(data.get("priority", 50)),
            created_at=str(data.get("created_at") or utc_now()),
            updated_at=str(data.get("updated_at") or utc_now()),
            payload=dict(data.get("payload") or {}),
            error=data.get("error"),
            approval_required=bool(data.get("approval_required", False)),
        )
