"""PostgreSQL-first persistence for the central long-running job runtime."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping
from uuid import uuid4

from secondbrain.jobs.models import Job, JobStatus, Lease, priority_rank


class JobRepositoryError(RuntimeError):
    pass


class JobVersionConflict(JobRepositoryError):
    pass


_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS runtime_jobs (
        job_id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL, job_type TEXT NOT NULL,
        status TEXT NOT NULL, priority_rank INTEGER NOT NULL, idempotency_key TEXT,
        version INTEGER NOT NULL, data TEXT NOT NULL,
        UNIQUE(workspace_id, idempotency_key)
    )""",
    """CREATE TABLE IF NOT EXISTS runtime_job_leases (
        lease_id TEXT PRIMARY KEY, job_id TEXT NOT NULL UNIQUE, worker_id TEXT NOT NULL,
        acquired_at TEXT NOT NULL, heartbeat_at TEXT NOT NULL, expires_at TEXT NOT NULL,
        version INTEGER NOT NULL, FOREIGN KEY(job_id) REFERENCES runtime_jobs(job_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_runtime_jobs_claim ON runtime_jobs(status, priority_rank, job_id)",
    "CREATE INDEX IF NOT EXISTS idx_runtime_jobs_workspace ON runtime_jobs(workspace_id, status)",
)


def _iso(value: datetime | None = None) -> str:
    return (value or datetime.now(timezone.utc)).isoformat(timespec="seconds")


class PostgresJobRepository:
    backend = "postgres"

    def __init__(self, executor: Any, *, lease_seconds: float = 60.0) -> None:
        self.executor = executor
        self.dialect = getattr(executor, "dialect", "postgresql")
        self.lease_seconds = lease_seconds
        self.lease_conflicts = 0

    def ensure_schema(self) -> None:
        with self._transaction() as tx:
            for statement in _SCHEMA:
                tx.execute(statement)

    def create_job(self, job: Job) -> Job:
        if not job.workspace_id or not job.payload_reference.strip():
            raise JobRepositoryError("job_identity_or_payload_reference_missing")
        job.created_at = job.created_at or _iso()
        job.updated_at = job.created_at
        params = self._params(job)
        try:
            self.executor.execute(
                "INSERT INTO runtime_jobs(job_id,workspace_id,job_type,status,priority_rank,"
                "idempotency_key,version,data) VALUES(:job_id,:workspace_id,:job_type,:status,"
                ":priority_rank,:idempotency_key,:version,:data)", params)
        except Exception as exc:
            raise JobRepositoryError("duplicate_job_or_idempotency_key") from exc
        return job

    def get_job(self, job_id: str, *, workspace_id: str) -> Job | None:
        rows = self.executor.execute(
            "SELECT data FROM runtime_jobs WHERE job_id=:job_id AND workspace_id=:workspace_id",
            {"job_id": job_id, "workspace_id": workspace_id})
        return Job.from_dict(json.loads(rows[0][0])) if rows else None

    def list_jobs(self, *, workspace_id: str, status: str | None = None) -> list[Job]:
        sql = "SELECT data FROM runtime_jobs WHERE workspace_id=:workspace_id"
        params: dict[str, Any] = {"workspace_id": workspace_id}
        if status:
            sql += " AND status=:status"
            params["status"] = status
        sql += " ORDER BY priority_rank DESC, job_id"
        return [Job.from_dict(json.loads(row[0])) for row in self.executor.execute(sql, params)]

    def claim_next_job(self, *, worker_id: str, workspace_id: str,
                       now: datetime | None = None) -> Job | None:
        moment = now or datetime.now(timezone.utc)
        lock = " FOR UPDATE SKIP LOCKED" if self.dialect == "postgresql" else ""
        with self._transaction() as tx:
            rows = tx.execute(
                "SELECT job_id,data FROM runtime_jobs WHERE workspace_id=:workspace_id "
                "AND status=:status ORDER BY priority_rank DESC, job_id LIMIT 1" + lock,
                {"workspace_id": workspace_id, "status": JobStatus.QUEUED.value})
            if not rows:
                return None
            job = Job.from_dict(json.loads(rows[0][1]))
            job.status = JobStatus.CLAIMED.value
            job.started_at = job.started_at or _iso(moment)
            job.lease = Lease(uuid4().hex, job.job_id, worker_id, _iso(moment),
                              _iso(moment + timedelta(seconds=self.lease_seconds)), _iso(moment))
            self._save(tx, job, expected_version=job.version)
            tx.execute(
                "INSERT INTO runtime_job_leases(lease_id,job_id,worker_id,acquired_at,heartbeat_at,"
                "expires_at,version) VALUES(:lease_id,:job_id,:worker_id,:acquired_at,:heartbeat_at,"
                ":expires_at,1)", job.lease.to_dict())
            return job

    def renew_lease(self, job_id: str, *, workspace_id: str, worker_id: str,
                    now: datetime | None = None) -> Job:
        job = self._required(job_id, workspace_id)
        self._require_owner(job, worker_id)
        moment = now or datetime.now(timezone.utc)
        job.lease.heartbeat_at = _iso(moment)
        job.lease.until = _iso(moment + timedelta(seconds=self.lease_seconds))
        with self._transaction() as tx:
            tx.execute("UPDATE runtime_job_leases SET heartbeat_at=:heartbeat_at,expires_at=:expires_at,"
                       "version=version+1 WHERE job_id=:job_id AND worker_id=:worker_id",
                       job.lease.to_dict())
            self._save(tx, job, job.version)
        return job

    def release_lease(self, job_id: str, *, workspace_id: str, worker_id: str) -> Job:
        job = self._required(job_id, workspace_id)
        self._require_owner(job, worker_id)
        with self._transaction() as tx:
            tx.execute("DELETE FROM runtime_job_leases WHERE job_id=:job_id AND worker_id=:worker_id",
                       {"job_id": job_id, "worker_id": worker_id})
            job.lease = Lease()
            self._save(tx, job, job.version)
        return job

    def update_progress(self, job_id: str, *, workspace_id: str, worker_id: str,
                        progress: float) -> Job:
        if not 0.0 <= progress <= 1.0:
            raise ValueError("progress_out_of_range")
        return self._mutate(job_id, workspace_id, worker_id, progress=float(progress))

    def save_checkpoint(self, job_id: str, *, workspace_id: str, worker_id: str,
                        checkpoint: Mapping[str, Any]) -> Job:
        return self._mutate(job_id, workspace_id, worker_id, checkpoint=dict(checkpoint))

    def complete_job(self, job_id: str, *, workspace_id: str, worker_id: str) -> Job:
        return self._finish(job_id, workspace_id, worker_id, JobStatus.COMPLETED.value,
                            progress=1.0, completed_at=_iso())

    def fail_job(self, job_id: str, *, workspace_id: str, worker_id: str,
                 error_code: str, error_summary: str) -> Job:
        job = self._required(job_id, workspace_id)
        self._require_owner(job, worker_id)
        job.attempts += 1
        if not job.idempotent:
            status = JobStatus.RECOVERY_REQUIRED.value
        elif job.attempts < job.max_attempts:
            status = JobStatus.RETRYING.value
        else:
            status = JobStatus.FAILED.value
        job = self._finish(job_id, workspace_id, worker_id, status, attempts=job.attempts,
                           error_code=error_code, error_summary=error_summary[:200])
        if status == JobStatus.RETRYING.value:
            job = self._set_status(job_id, workspace_id, JobStatus.QUEUED.value)
        return job

    def start_job(self, job_id: str, *, workspace_id: str, worker_id: str) -> Job:
        return self._mutate(job_id, workspace_id, worker_id, status=JobStatus.RUNNING.value)

    def pause_job(self, job_id: str, *, workspace_id: str) -> Job:
        return self._set_status(job_id, workspace_id, JobStatus.PAUSED.value)

    def resume_job(self, job_id: str, *, workspace_id: str) -> Job:
        return self._set_status(job_id, workspace_id, JobStatus.QUEUED.value)

    def cancel_job(self, job_id: str, *, workspace_id: str) -> Job:
        return self._set_status(job_id, workspace_id, JobStatus.CANCELLED.value)

    def recover_expired_jobs(self, *, now: datetime | None = None) -> list[str]:
        moment = _iso(now)
        rows = self.executor.execute(
            "SELECT j.data FROM runtime_jobs j JOIN runtime_job_leases l ON l.job_id=j.job_id "
            "WHERE l.expires_at < :now", {"now": moment})
        recovered = []
        for row in rows:
            job = Job.from_dict(json.loads(row[0]))
            status = JobStatus.QUEUED.value if job.idempotent else JobStatus.RECOVERY_REQUIRED.value
            self._set_status(job.job_id, job.workspace_id, status)
            recovered.append(job.job_id)
        return recovered

    def _mutate(self, job_id: str, workspace_id: str, worker_id: str, **changes: Any) -> Job:
        job = self._required(job_id, workspace_id)
        self._require_owner(job, worker_id)
        for key, value in changes.items():
            setattr(job, key, value)
        self._save(self.executor, job, job.version)
        return job

    def _finish(self, job_id: str, workspace_id: str, worker_id: str,
                status: str, **changes: Any) -> Job:
        self._mutate(job_id, workspace_id, worker_id, status=status, **changes)
        return self.release_lease(job_id, workspace_id=workspace_id, worker_id=worker_id)

    def _set_status(self, job_id: str, workspace_id: str, status: str) -> Job:
        job = self._required(job_id, workspace_id)
        job.status = status
        with self._transaction() as tx:
            tx.execute("DELETE FROM runtime_job_leases WHERE job_id=:job_id", {"job_id": job_id})
            job.lease = Lease()
            self._save(tx, job, job.version)
        return job

    def _required(self, job_id: str, workspace_id: str) -> Job:
        job = self.get_job(job_id, workspace_id=workspace_id)
        if job is None:
            raise KeyError("unknown_job")
        return job

    def _require_owner(self, job: Job, worker_id: str) -> None:
        if not job.lease.worker_id or job.lease.worker_id != worker_id:
            self.lease_conflicts += 1
            raise PermissionError("lease_held_by_other_worker")

    def _save(self, tx: Any, job: Job, expected_version: int) -> None:
        job.version = expected_version + 1
        job.updated_at = _iso()
        params = self._params(job)
        params["expected_version"] = expected_version
        rows = tx.execute("SELECT version FROM runtime_jobs WHERE job_id=:job_id AND workspace_id=:workspace_id",
                          params)
        if not rows or int(rows[0][0]) != expected_version:
            raise JobVersionConflict("stale_job_version")
        updated = tx.execute(
            "UPDATE runtime_jobs SET status=:status,priority_rank=:priority_rank,version=:version,"
            "data=:data WHERE job_id=:job_id AND workspace_id=:workspace_id "
            "AND version=:expected_version RETURNING version", params)
        if not updated:
            raise JobVersionConflict("stale_job_version")

    @staticmethod
    def _params(job: Job) -> dict[str, Any]:
        return {"job_id": job.job_id, "workspace_id": job.workspace_id, "job_type": job.type,
                "status": job.status, "priority_rank": priority_rank(job.priority),
                "idempotency_key": job.idempotency_key or None, "version": job.version,
                "data": json.dumps(job.to_dict(), ensure_ascii=False, sort_keys=True)}

    @contextmanager
    def _transaction(self):
        database = getattr(self.executor, "database", None)
        if database is None:
            with self.executor.transaction() as tx:
                yield tx
            return
        from sqlalchemy import text
        with database.session() as session:
            class SessionExecutor:
                @staticmethod
                def execute(sql: str, params: Mapping[str, Any] | None = None):
                    result = session.execute(text(sql), dict(params or {}))
                    return [tuple(row) for row in result.fetchall()] if result.returns_rows else []
            yield SessionExecutor()


def create_job_repository(*, env: Mapping[str, str] | None = None,
                          executor: Any | None = None) -> PostgresJobRepository | None:
    values = env if env is not None else os.environ
    profile = str(values.get("SECONDBRAIN_ENV") or "development").lower()
    backend = str(values.get("JOB_REPOSITORY_BACKEND") or
                  ("postgres" if profile.startswith("prod") else "jsonl")).lower()
    if backend == "jsonl":
        if profile.startswith("prod"):
            raise JobRepositoryError("jsonl_not_allowed_in_production")
        return None
    if backend != "postgres":
        raise JobRepositoryError(f"unknown_job_repository_backend:{backend}")
    if executor is None:
        url = str(values.get("SECOND_BRAIN_DATABASE_URL") or values.get("DATABASE_URL") or "").strip()
        if not url:
            raise JobRepositoryError("postgres_job_repository_requires_database_url")
        from secondbrain.storage.database import Database
        from secondbrain.storage.database_config import DatabaseConfig
        from secondbrain.storage.db_executor import SqlAlchemyExecutor
        executor = SqlAlchemyExecutor(Database(DatabaseConfig(url=url)))
    repository = PostgresJobRepository(executor)
    repository.ensure_schema()
    return repository
