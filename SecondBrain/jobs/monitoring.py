"""Content-free operational metrics for the central job runtime."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from secondbrain.jobs.models import JobStatus


def _parse(value: str) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int((len(ordered) - 1) * percentile)))
    return round(ordered[index], 3)


class JobMetrics:
    def __init__(self, repository: Any, worker_registry: Any | None = None) -> None:
        self.repository = repository
        self.worker_registry = worker_registry

    def snapshot(self, *, workspace_id: str, now: datetime | None = None) -> dict[str, Any]:
        moment = now or datetime.now(timezone.utc)
        jobs = self.repository.list_jobs(workspace_id=workspace_id)
        waits: list[float] = []
        runtimes: list[float] = []
        by_type: dict[str, int] = {}
        for job in jobs:
            by_type[job.type] = by_type.get(job.type, 0) + 1
            created, started = _parse(job.created_at), _parse(job.started_at)
            completed = _parse(job.completed_at)
            if created and started:
                waits.append(max(0.0, (started - created).total_seconds()))
            if started:
                runtimes.append(max(0.0, ((completed or moment) - started).total_seconds()))
        total = len(jobs)
        failures = sum(job.status == JobStatus.FAILED.value for job in jobs)
        return {
            "queue_length": sum(job.status == JobStatus.QUEUED.value for job in jobs),
            "average_wait_seconds": round(sum(waits) / len(waits), 3) if waits else 0.0,
            "p95_wait_seconds": _percentile(waits, 0.95),
            "average_runtime_seconds": round(sum(runtimes) / len(runtimes), 3) if runtimes else 0.0,
            "retry_rate": round(sum(job.attempts > 0 for job in jobs) / total, 4) if total else 0.0,
            "failure_rate": round(failures / total, 4) if total else 0.0,
            "lease_conflicts": int(getattr(self.repository, "lease_conflicts", 0)),
            "recovery_jobs": sum(job.status == JobStatus.RECOVERY_REQUIRED.value for job in jobs),
            "worker_health": self.worker_registry.snapshot() if self.worker_registry else [],
            "jobs_per_type": by_type,
        }
