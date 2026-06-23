from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from .events import DesktopEvent, EventBus, EventType
from .notifications import NotificationCenter, NotificationLevel
from .status_service import StatusColor, StatusService


class JobState(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class JobFeedback:
    id: str
    name: str
    state: JobState
    message: str = ""
    progress: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def terminal(self) -> bool:
        return self.state in {JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED}


class JobFeedbackCenter:
    """Tracks desktop job state and mirrors it into events, notifications and status.

    The class is UI-toolkit agnostic. It gives the shell a single source of truth for
    running/background actions while preserving deterministic side effects for tests.
    """

    def __init__(
        self,
        events: EventBus,
        notifications: NotificationCenter,
        status: StatusService,
        status_name: str = "Jobs",
    ) -> None:
        self.events = events
        self.notifications = notifications
        self.status = status
        self.status_name = status_name
        self._jobs: dict[str, JobFeedback] = {}
        self.status.set_status(status_name, StatusColor.GREEN, "idle")

    def start(self, name: str, message: str = "", metadata: dict[str, Any] | None = None) -> JobFeedback:
        job = JobFeedback(
            id=uuid4().hex,
            name=name,
            state=JobState.RUNNING,
            message=message,
            progress=0.0,
            metadata=dict(metadata or {}),
        )
        self._jobs[job.id] = job
        self.status.set_status(self.status_name, StatusColor.YELLOW, f"running {name}")
        self.events.publish(DesktopEvent(EventType.JOB_STARTED, {"job_id": job.id, "name": name}))
        self.notifications.push("Job started", name, NotificationLevel.INFO)
        return job

    def progress(self, job_id: str, progress: float, message: str = "") -> JobFeedback:
        job = self._require_job(job_id)
        bounded = max(0.0, min(1.0, progress))
        updated = self._replace(job, state=JobState.RUNNING, progress=bounded, message=message or job.message)
        self.status.set_status(self.status_name, StatusColor.YELLOW, f"{updated.name} {int(bounded * 100)}%")
        return updated

    def succeed(self, job_id: str, message: str = "completed") -> JobFeedback:
        job = self._require_job(job_id)
        updated = self._replace(job, state=JobState.SUCCEEDED, progress=1.0, message=message)
        self.notifications.push("Job completed", job.name, NotificationLevel.SUCCESS)
        self.events.publish(DesktopEvent(EventType.JOB_FINISHED, {"job_id": job.id, "name": job.name, "ok": True}))
        self._refresh_overall_status()
        return updated

    def fail(self, job_id: str, error: str) -> JobFeedback:
        job = self._require_job(job_id)
        updated = self._replace(job, state=JobState.FAILED, message=error)
        self.notifications.push("Job failed", f"{job.name}: {error}", NotificationLevel.ERROR)
        self.events.publish(DesktopEvent(EventType.ERROR_OCCURRED, {"job_id": job.id, "name": job.name, "error": error}))
        self.events.publish(DesktopEvent(EventType.JOB_FINISHED, {"job_id": job.id, "name": job.name, "ok": False}))
        self.status.set_status(self.status_name, StatusColor.RED, f"failed {job.name}")
        return updated

    def cancel(self, job_id: str, message: str = "cancelled") -> JobFeedback:
        job = self._require_job(job_id)
        updated = self._replace(job, state=JobState.CANCELLED, message=message)
        self.notifications.push("Job cancelled", job.name, NotificationLevel.WARNING)
        self.events.publish(DesktopEvent(EventType.JOB_FINISHED, {"job_id": job.id, "name": job.name, "ok": False, "cancelled": True}))
        self._refresh_overall_status()
        return updated

    def get(self, job_id: str) -> JobFeedback | None:
        return self._jobs.get(job_id)

    def list(self, active_only: bool = False) -> list[JobFeedback]:
        jobs = list(self._jobs.values())
        if active_only:
            return [job for job in jobs if not job.terminal]
        return jobs

    def _replace(self, job: JobFeedback, **changes: Any) -> JobFeedback:
        data = {
            "id": job.id,
            "name": job.name,
            "state": job.state,
            "message": job.message,
            "progress": job.progress,
            "metadata": dict(job.metadata),
            "created_at": job.created_at,
            "updated_at": datetime.now(timezone.utc),
        }
        data.update(changes)
        updated = JobFeedback(**data)
        self._jobs[job.id] = updated
        return updated

    def _require_job(self, job_id: str) -> JobFeedback:
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(f"Unknown job: {job_id}")
        return job

    def _refresh_overall_status(self) -> None:
        active = self.list(active_only=True)
        if active:
            self.status.set_status(self.status_name, StatusColor.YELLOW, f"{len(active)} running")
        else:
            self.status.set_status(self.status_name, StatusColor.GREEN, "idle")
