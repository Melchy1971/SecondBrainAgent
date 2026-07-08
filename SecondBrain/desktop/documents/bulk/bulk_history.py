"""In-memory bulk job history."""
from __future__ import annotations

from .bulk_job import BulkJob


class BulkHistory:
    def __init__(self) -> None:
        self._jobs: dict[str, BulkJob] = {}

    def record(self, job: BulkJob) -> BulkJob:
        self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> BulkJob | None:
        return self._jobs.get(job_id)

    def list(self) -> list[BulkJob]:
        return list(self._jobs.values())

    def failed(self) -> list[BulkJob]:
        return [job for job in self._jobs.values() if job.failed_items > 0]
