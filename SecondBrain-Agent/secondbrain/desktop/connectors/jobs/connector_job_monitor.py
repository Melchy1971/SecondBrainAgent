from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .connector_job_history import ConnectorJobHistory
from .connector_job_models import ConnectorJob, ConnectorJobState


@dataclass(frozen=True)
class ConnectorJobSnapshot:
    total_jobs: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int
    cancelled_jobs: int
    last_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_jobs": self.total_jobs,
            "running_jobs": self.running_jobs,
            "completed_jobs": self.completed_jobs,
            "failed_jobs": self.failed_jobs,
            "cancelled_jobs": self.cancelled_jobs,
            "last_error": self.last_error,
        }


class ConnectorJobMonitor:
    def __init__(self, history: ConnectorJobHistory) -> None:
        self.history = history

    def snapshot(self, *, connector_id: str | None = None, active_jobs: list[ConnectorJob] | None = None) -> ConnectorJobSnapshot:
        jobs = self.history.list(connector_id=connector_id)
        if active_jobs:
            jobs = jobs + [job for job in active_jobs if connector_id is None or job.connector_id == connector_id]
        last_error = next((job.error for job in reversed(jobs) if job.error), None)
        return ConnectorJobSnapshot(
            total_jobs=len(jobs),
            running_jobs=sum(1 for job in jobs if job.state == ConnectorJobState.RUNNING),
            completed_jobs=sum(1 for job in jobs if job.state == ConnectorJobState.COMPLETED),
            failed_jobs=sum(1 for job in jobs if job.state == ConnectorJobState.FAILED),
            cancelled_jobs=sum(1 for job in jobs if job.state == ConnectorJobState.CANCELLED),
            last_error=last_error,
        )
