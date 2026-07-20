from __future__ import annotations

from typing import Any

from secondbrain.native.job_queue_center.service import JobQueueService


class JobSurface:
    """Payload-free read projection of the workspace-local native job queue."""

    def __init__(self, service: JobQueueService, *, limit: int = 100) -> None:
        self.service = service
        self.limit = max(1, min(int(limit), 500))

    def snapshot(self) -> dict[str, Any]:
        jobs = self.service.list_jobs()
        items = [
            {
                "job_id": job.id,
                "kind": job.kind,
                "title": job.title,
                "status": job.status,
                "priority": job.priority,
                "attempts": job.attempts,
                "max_attempts": job.max_attempts,
                "approval_required": job.approval_required,
                "created_at": job.created_at,
                "updated_at": job.updated_at,
            }
            for job in jobs[: self.limit]
        ]
        counts: dict[str, int] = {}
        for job in jobs:
            counts[job.status] = counts.get(job.status, 0) + 1
        return {
            "status": "ready",
            "total": len(jobs),
            "visible_count": len(items),
            "running_count": counts.get("running", 0),
            "blocked_count": counts.get("blocked", 0),
            "counts": counts,
            "items": items,
            "payloads_exposed": False,
            "workspace_isolated": True,
        }
