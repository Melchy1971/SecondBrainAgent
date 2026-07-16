"""Data model for persistent long-running jobs.

A job is a restart-survivable unit of background work. It stores only a
reference to its payload (never the full payload) so the queue stays small and
free of sensitive data, plus a checkpoint for resumable progress, a lease for
crash detection, an idempotency key to prevent double execution, and its
approval state so a pending gate is never lost across a restart.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

__all__ = ["JobType", "JobStatus", "JobPriority", "Lease", "JobLease", "Job",
           "NON_IDEMPOTENT_TYPES", "priority_rank"]


class JobType(StrEnum):
    IMPORT = "import"
    CONNECTOR_SYNC = "connector_sync"
    EMBEDDING = "embedding"
    REINDEX = "reindex"
    GRAPH_EXTRACTION = "graph_extraction"
    MEMORY_CONSOLIDATION = "memory_consolidation"
    AGENT_PLAN = "agent_plan"
    BACKUP = "backup"
    RESTORE = "restore"
    DIAGNOSTICS = "diagnostics"


class JobStatus(StrEnum):
    QUEUED = "queued"
    CLAIMED = "claimed"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RECOVERY_REQUIRED = "recovery_required"


class JobPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


_PRIORITY_RANK = {JobPriority.LOW.value: 0, JobPriority.NORMAL.value: 10,
                  JobPriority.HIGH.value: 20, JobPriority.CRITICAL.value: 30}


def priority_rank(value: str | int) -> int:
    if isinstance(value, int):
        return value
    return _PRIORITY_RANK.get(str(value).lower(), _PRIORITY_RANK[JobPriority.NORMAL.value])


# Types whose steps may cause irreversible external effects (send/delete inside
# an agent plan, or a restore) and therefore must never be auto-retried.
NON_IDEMPOTENT_TYPES: frozenset[str] = frozenset({JobType.AGENT_PLAN.value, JobType.RESTORE.value})


@dataclass
class Lease:
    lease_id: str = ""
    job_id: str = ""
    worker_id: str = ""
    acquired_at: str = ""
    until: str = ""          # ISO expiry; empty == no active lease
    heartbeat_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"lease_id": self.lease_id, "job_id": self.job_id, "owner": self.worker_id,
                "worker_id": self.worker_id, "acquired_at": self.acquired_at,
                "until": self.until, "expires_at": self.until, "heartbeat_at": self.heartbeat_at}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Lease":
        return cls(lease_id=data.get("lease_id", ""), job_id=data.get("job_id", ""),
                   worker_id=data.get("owner", data.get("worker_id", "")), acquired_at=data.get("acquired_at", ""),
                   until=data.get("expires_at", data.get("until", "")),
                   heartbeat_at=data.get("heartbeat_at", ""))


JobLease = Lease


@dataclass
class Job:
    job_id: str
    type: str
    workspace_id: str
    status: str = JobStatus.QUEUED.value
    priority: str | int = JobPriority.NORMAL.value
    payload_reference: str = ""             # pointer only - never the payload
    progress: float = 0.0
    checkpoint: dict[str, Any] = field(default_factory=dict)
    attempts: int = 0
    max_attempts: int = 3
    idempotency_key: str = ""
    idempotent: bool = True
    approval_required: bool = False
    approved: bool = False
    lease: Lease = field(default_factory=Lease)
    created_at: str = ""
    updated_at: str = ""
    completed_at: str = ""
    started_at: str = ""
    error_code: str = ""
    error_summary: str = ""
    version: int = 1
    error: str = ""

    @property
    def job_type(self) -> str:
        return self.type

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id, "type": self.type, "workspace_id": self.workspace_id,
            "status": self.status, "priority": self.priority, "payload_reference": self.payload_reference,
            "progress": round(float(self.progress), 3), "checkpoint": dict(self.checkpoint),
            "attempts": self.attempts, "max_attempts": self.max_attempts,
            "idempotency_key": self.idempotency_key, "idempotent": self.idempotent,
            "approval_required": self.approval_required, "approved": self.approved,
            "lease": self.lease.to_dict(), "created_at": self.created_at, "updated_at": self.updated_at,
            "completed_at": self.completed_at, "error": self.error,
            "started_at": self.started_at, "error_code": self.error_code,
            "error_summary": self.error_summary, "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Job":
        return cls(
            job_id=data["job_id"], type=data.get("type", JobType.IMPORT.value),
            workspace_id=data.get("workspace_id", ""), status=data.get("status", JobStatus.QUEUED.value),
            priority=data.get("priority", JobPriority.NORMAL.value),
            payload_reference=data.get("payload_reference", ""),
            progress=float(data.get("progress", 0.0)), checkpoint=dict(data.get("checkpoint", {})),
            attempts=int(data.get("attempts", 0)), max_attempts=int(data.get("max_attempts", 3)),
            idempotency_key=data.get("idempotency_key", ""), idempotent=bool(data.get("idempotent", True)),
            approval_required=bool(data.get("approval_required", False)), approved=bool(data.get("approved", False)),
            lease=Lease.from_dict(data.get("lease", {})), created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""), completed_at=data.get("completed_at", ""),
            error=data.get("error", ""),
            started_at=data.get("started_at", ""), error_code=data.get("error_code", ""),
            error_summary=data.get("error_summary", ""), version=int(data.get("version", 1)),
        )
