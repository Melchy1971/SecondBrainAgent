from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Iterable

from .models import QueueJob, JobKind, JobStatus, utc_now


class JobQueueService:
    """Small persistent JSONL queue for native runtime jobs.

    The service intentionally does not execute dangerous work directly. It provides
    one observable queue surface for GUI, voice actions, imports, reindex jobs,
    update jobs, and approval-gated actions.
    """

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or ".").resolve()
        self.runtime_dir = self.root / "runtime" / "native" / "job_queue"
        self.queue_path = self.runtime_dir / "jobs.jsonl"
        self.history_path = self.runtime_dir / "job_history.jsonl"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)

    def add_job(self, kind: JobKind, title: str, *, priority: int = 50, approval_required: bool = False, payload: dict | None = None) -> QueueJob:
        job = QueueJob.create(kind, title, priority=priority, payload=payload, approval_required=approval_required)
        self._append(self.queue_path, job.to_dict())
        self._append(self.history_path, {"event": "created", **job.to_dict()})
        return job

    def list_jobs(self, *, status: JobStatus | None = None, kind: JobKind | None = None) -> list[QueueJob]:
        jobs = self._read_jobs()
        if status:
            jobs = [job for job in jobs if job.status == status]
        if kind:
            jobs = [job for job in jobs if job.kind == kind]
        return sorted(jobs, key=lambda item: (item.status != "running", item.status != "pending", item.priority, item.created_at))

    def get_job(self, job_id: str) -> QueueJob | None:
        return next((job for job in self._read_jobs() if job.id == job_id), None)

    def update_status(self, job_id: str, status: JobStatus, *, error: str | None = None) -> QueueJob:
        jobs = self._read_jobs()
        updated: QueueJob | None = None
        next_jobs: list[QueueJob] = []
        for job in jobs:
            if job.id == job_id:
                updated = replace(job, status=status, error=error, updated_at=utc_now())
                next_jobs.append(updated)
            else:
                next_jobs.append(job)
        if updated is None:
            raise KeyError(f"Job nicht gefunden: {job_id}")
        self._write_jobs(next_jobs)
        self._append(self.history_path, {"event": "status", **updated.to_dict()})
        return updated

    def approve(self, job_id: str) -> QueueJob:
        job = self.get_job(job_id)
        if job is None:
            raise KeyError(f"Job nicht gefunden: {job_id}")
        if not job.approval_required:
            return job
        return self.update_status(job_id, "pending")

    def cancel(self, job_id: str) -> QueueJob:
        return self.update_status(job_id, "cancelled")

    def clear_finished(self) -> int:
        jobs = self._read_jobs()
        keep = [job for job in jobs if job.status not in {"success", "failed", "cancelled"}]
        removed = len(jobs) - len(keep)
        self._write_jobs(keep)
        self._append(self.history_path, {"event": "clear_finished", "removed": removed, "created_at": utc_now()})
        return removed

    def snapshot(self) -> dict:
        jobs = self._read_jobs()
        counts: dict[str, int] = {}
        for job in jobs:
            counts[job.status] = counts.get(job.status, 0) + 1
        blocked = [job for job in jobs if job.status == "blocked"]
        running = [job for job in jobs if job.status == "running"]
        return {
            "version": "30.44",
            "queue_path": str(self.queue_path),
            "total": len(jobs),
            "counts": counts,
            "blocked": len(blocked),
            "running": len(running),
            "health": "blocked" if blocked else ("busy" if running else "ok"),
            "jobs": [job.to_dict() for job in self.list_jobs()],
        }

    def _read_jobs(self) -> list[QueueJob]:
        if not self.queue_path.exists():
            return []
        result: list[QueueJob] = []
        for line in self.queue_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            result.append(QueueJob.from_dict(json.loads(line)))
        return result

    def _write_jobs(self, jobs: Iterable[QueueJob]) -> None:
        self.queue_path.write_text("\n".join(json.dumps(job.to_dict(), ensure_ascii=False, sort_keys=True) for job in jobs) + ("\n" if jobs else ""), encoding="utf-8")

    @staticmethod
    def _append(path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(data, ensure_ascii=False, sort_keys=True) + "\n")
