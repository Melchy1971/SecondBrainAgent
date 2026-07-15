"""Persistent long-running job execution.

``JobStore`` persists every job as one JSON line so state survives a restart.
``JobManager`` runs the queue: priority dispatch, lease + heartbeat so a crashed
worker is detected, checkpointed resume, bounded retry with backoff, and an
exactly-once guard keyed on ``idempotency_key``. Non-idempotent jobs
(agent plans, restores) are never auto-retried - they go to review. Approval
state and workspace isolation are preserved across every transition.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Iterable, Mapping

from secondbrain.jobs.models import Job, JobStatus, JobType, Lease, NON_IDEMPOTENT_TYPES

__all__ = ["JobStore", "JobManager"]

_STORE_LOCKS: dict[str, threading.RLock] = {}
_STORE_LOCKS_GUARD = threading.Lock()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def _parse(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


class JobStore:
    """JSONL-backed job repository. The whole set is rewritten atomically on
    each mutation - small volume, and it keeps the file consistent after a
    crash (temp file + os.replace)."""

    def __init__(self, path: str) -> None:
        self.path = os.path.abspath(path)
        self._jobs: dict[str, Job] = {}
        with _STORE_LOCKS_GUARD:
            self.lock = _STORE_LOCKS.setdefault(self.path, threading.RLock())
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        with open(self.path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    job = Job.from_dict(json.loads(line))
                except (json.JSONDecodeError, KeyError):
                    continue
                self._jobs[job.job_id] = job

    def _flush(self) -> None:
        directory = os.path.dirname(self.path) or "."
        os.makedirs(directory, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                for job in self._jobs.values():
                    fh.write(json.dumps(job.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def put(self, job: Job) -> None:
        with self.lock:
            job.updated_at = _iso(_now())
            job.version += 1
            self._jobs[job.job_id] = job
            self._flush()

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def all(self, *, workspace_id: str | None = None) -> list[Job]:
        return [j for j in self._jobs.values() if workspace_id is None or j.workspace_id == workspace_id]


class JobManager:
    def __init__(self, store: JobStore, *, lease_seconds: float = 60.0) -> None:
        self.store = store
        self.lease_seconds = lease_seconds
        self._completed_keys: set[str] = {
            j.idempotency_key for j in store.all()
            if j.status == JobStatus.COMPLETED.value and j.idempotency_key
        }

    # -- enqueue ----------------------------------------------------------

    def enqueue(self, *, type: str, workspace_id: str, payload_reference: str, priority: int = 0,
                idempotency_key: str = "", idempotent: bool | None = None,
                approval_required: bool = False, max_attempts: int = 3) -> Job:
        from uuid import uuid4
        is_idem = (type not in NON_IDEMPOTENT_TYPES) if idempotent is None else bool(idempotent)
        job = Job(
            job_id=str(uuid4()), type=type, workspace_id=workspace_id,
            status=JobStatus.WAITING_FOR_APPROVAL.value if approval_required else JobStatus.QUEUED.value,
            priority=priority, payload_reference=payload_reference,
            idempotency_key=idempotency_key, idempotent=is_idem,
            approval_required=approval_required, max_attempts=max_attempts, created_at=_iso(_now()),
        )
        self.store.put(job)
        return job

    def approve(self, job_id: str, *, approval_authority: Any) -> Job:
        job = self.store.get(job_id)
        if job is None:
            raise KeyError("unknown_job")
        if approval_authority is None or not approval_authority.claim(job=job):
            raise PermissionError("bound_approval_required")
        job.approved = True
        if job.status == JobStatus.WAITING_FOR_APPROVAL.value:
            job.status = JobStatus.QUEUED.value
        self.store.put(job)
        return job

    # -- dispatch ---------------------------------------------------------

    def claim(self, *, worker_id: str, workspace_id: str | None = None, now: datetime | None = None) -> Job | None:
        from uuid import uuid4
        moment = now or _now()
        with self.store.lock:
            self.store._jobs.clear()
            self.store._load()
            candidates = [j for j in self.store.all(workspace_id=workspace_id)
                          if j.status == JobStatus.QUEUED.value
                          and (not j.approval_required or j.approved)]
            if not candidates:
                return None
            candidates.sort(key=lambda j: (-j.priority, j.created_at))
            job = candidates[0]
            if not job.payload_reference.strip():
                job.status, job.error_code, job.error_summary = JobStatus.FAILED.value, "invalid_payload_reference", "payload reference missing"
                self.store.put(job)
                return None
            job.status = JobStatus.RUNNING.value
            job.started_at = job.started_at or _iso(moment)
            job.lease = Lease(lease_id=uuid4().hex, job_id=job.job_id, worker_id=worker_id,
                              acquired_at=_iso(moment), until=_iso(moment + timedelta(seconds=self.lease_seconds)),
                              heartbeat_at=_iso(moment))
            self.store.put(job)
            return job

    def heartbeat(self, job_id: str, worker_id: str, *, now: datetime | None = None) -> None:
        job = self._owned(job_id, worker_id)
        moment = now or _now()
        job.lease.heartbeat_at = _iso(moment)
        job.lease.until = _iso(moment + timedelta(seconds=self.lease_seconds))
        self.store.put(job)

    def checkpoint(self, job_id: str, worker_id: str, data: Mapping[str, Any], *, progress: float | None = None) -> None:
        job = self._owned(job_id, worker_id)
        job.checkpoint = dict(data)
        if progress is not None:
            job.progress = float(progress)
        self.store.put(job)

    # -- completion / failure --------------------------------------------

    def complete(self, job_id: str, worker_id: str, *, now: datetime | None = None) -> dict[str, Any]:
        job = self.store.get(job_id)
        if job is None:
            raise KeyError("unknown_job")
        if job.status == JobStatus.COMPLETED.value:
            return {"status": "duplicate"}  # exactly-once
        self._owned(job_id, worker_id)
        if job.idempotency_key and job.idempotency_key in self._completed_keys and job.status != JobStatus.RUNNING.value:
            return {"status": "duplicate"}
        job.status = JobStatus.COMPLETED.value
        job.progress = 1.0
        job.completed_at = _iso(now or _now())
        job.lease = Lease()
        if job.idempotency_key:
            self._completed_keys.add(job.idempotency_key)
        self.store.put(job)
        return {"status": "completed"}

    def fail(self, job_id: str, worker_id: str, error: str, *, now: datetime | None = None) -> dict[str, Any]:
        job = self.store.get(job_id)
        if job is None:
            raise KeyError("unknown_job")
        job.attempts += 1
        job.error = error
        job.error_code = "job_execution_failed"
        job.error_summary = str(error)[:200]
        job.lease = Lease()
        if not job.idempotent:
            job.status = JobStatus.RECOVERY_REQUIRED.value  # never auto-retry
            self.store.put(job)
            return {"status": "recovery_required", "reason": "non_idempotent_needs_review"}
        if job.attempts >= job.max_attempts:
            job.status = JobStatus.FAILED.value
            self.store.put(job)
            return {"status": "failed"}
        job.status = JobStatus.QUEUED.value
        self.store.put(job)
        backoff = self._backoff(job.attempts)
        return {"status": "retrying", "attempt": job.attempts, "backoff_seconds": backoff}

    # -- lifecycle --------------------------------------------------------

    def pause(self, job_id: str) -> None:
        job = self.store.get(job_id)
        if job and job.status in (JobStatus.QUEUED.value, JobStatus.RUNNING.value):
            job.status = JobStatus.PAUSED.value
            job.lease = Lease()
            self.store.put(job)

    def resume(self, job_id: str) -> None:
        job = self.store.get(job_id)
        if job and job.status == JobStatus.PAUSED.value:
            job.status = JobStatus.QUEUED.value  # checkpoint retained -> continues
            self.store.put(job)

    def cancel(self, job_id: str) -> None:
        job = self.store.get(job_id)
        if job and job.status not in (JobStatus.COMPLETED.value, JobStatus.CANCELLED.value):
            job.status = JobStatus.CANCELLED.value
            job.lease = Lease()
            self.store.put(job)

    # -- crash recovery ---------------------------------------------------

    def recover_stale(self, *, now: datetime | None = None) -> list[str]:
        """Reclaim jobs whose worker crashed (running with an expired lease).
        Idempotent jobs are requeued and resume from their checkpoint;
        non-idempotent jobs require review."""
        moment = now or _now()
        recovered: list[str] = []
        for job in self.store.all():
            if job.status != JobStatus.RUNNING.value:
                continue
            until = _parse(job.lease.until)
            if until is not None and moment <= until:
                continue  # lease still valid
            if job.idempotent:
                job.status = JobStatus.QUEUED.value
            else:
                job.status = JobStatus.RECOVERY_REQUIRED.value
            job.lease = Lease()
            self.store.put(job)
            recovered.append(job.job_id)
        return recovered

    def graceful_shutdown(self, worker_id: str) -> list[str]:
        paused = []
        for job in self.store.all():
            if job.status == JobStatus.RUNNING.value and job.lease.worker_id == worker_id:
                job.status = JobStatus.QUEUED.value if job.idempotent else JobStatus.RECOVERY_REQUIRED.value
                job.lease = Lease()
                self.store.put(job)
                paused.append(job.job_id)
        return paused

    def metrics(self, *, workspace_id: str | None = None) -> dict[str, Any]:
        jobs = self.store.all(workspace_id=workspace_id)
        return {"queue_length": sum(job.status == JobStatus.QUEUED.value for job in jobs),
                "retries": sum(job.attempts for job in jobs),
                "failures": sum(job.status == JobStatus.FAILED.value for job in jobs),
                "recovery_jobs": sum(job.status == JobStatus.RECOVERY_REQUIRED.value for job in jobs)}

    # -- helpers ----------------------------------------------------------

    def queue_snapshot(self, *, workspace_id: str | None = None) -> list[Job]:
        jobs = [j for j in self.store.all(workspace_id=workspace_id)
                if j.status in (JobStatus.QUEUED.value, JobStatus.RUNNING.value,
                                JobStatus.RETRYING.value, JobStatus.WAITING_FOR_APPROVAL.value)]
        jobs.sort(key=lambda j: (-j.priority, j.created_at))
        return jobs

    @staticmethod
    def _backoff(attempt: int) -> float:
        return min(300.0, 2.0 ** attempt)

    def _owned(self, job_id: str, worker_id: str) -> Job:
        job = self.store.get(job_id)
        if job is None:
            raise KeyError("unknown_job")
        if job.lease.worker_id and job.lease.worker_id != worker_id:
            raise PermissionError("lease_held_by_other_worker")
        return job
