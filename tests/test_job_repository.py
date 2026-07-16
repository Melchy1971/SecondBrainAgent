from datetime import datetime, timedelta, timezone

import pytest

from secondbrain.jobs.models import Job, JobPriority, JobStatus, JobType
from secondbrain.jobs.repository import JobRepositoryError, PostgresJobRepository, create_job_repository
from secondbrain.storage.db_executor import SqliteExecutor


def _repo(tmp_path):
    executor = SqliteExecutor(str(tmp_path / "jobs.sqlite"))
    repository = PostgresJobRepository(executor, lease_seconds=10)
    repository.ensure_schema()
    return repository


def _job(job_id="j1", workspace="ws-1", priority=JobPriority.NORMAL.value, idem="key-1"):
    return Job(job_id=job_id, type=JobType.IMPORT.value, workspace_id=workspace,
               priority=priority, payload_reference=f"payload://{job_id}", idempotency_key=idem)


def test_claim_is_workspace_scoped_prioritized_and_leased(tmp_path):
    repo = _repo(tmp_path)
    repo.create_job(_job("low", priority=JobPriority.LOW.value, idem="low"))
    repo.create_job(_job("high", priority=JobPriority.HIGH.value, idem="high"))
    repo.create_job(_job("other", workspace="ws-2", priority=JobPriority.CRITICAL.value, idem="other"))
    claimed = repo.claim_next_job(worker_id="w1", workspace_id="ws-1")
    assert claimed.job_id == "high"
    assert claimed.status == JobStatus.CLAIMED.value
    assert claimed.lease.worker_id == "w1"
    assert repo.get_job("other", workspace_id="ws-1") is None


def test_checkpoint_progress_completion_and_idempotency(tmp_path):
    repo = _repo(tmp_path)
    repo.create_job(_job())
    claimed = repo.claim_next_job(worker_id="w1", workspace_id="ws-1")
    repo.save_checkpoint(claimed.job_id, workspace_id="ws-1", worker_id="w1", checkpoint={"offset": 4})
    repo.update_progress(claimed.job_id, workspace_id="ws-1", worker_id="w1", progress=0.5)
    completed = repo.complete_job(claimed.job_id, workspace_id="ws-1", worker_id="w1")
    assert completed.status == JobStatus.COMPLETED.value
    assert completed.checkpoint == {"offset": 4} and completed.progress == 1.0
    with pytest.raises(JobRepositoryError):
        repo.create_job(_job("duplicate", idem="key-1"))


def test_expired_recovery_respects_idempotency(tmp_path):
    repo = _repo(tmp_path)
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    repo.create_job(_job("safe", idem="safe"))
    unsafe = _job("unsafe", idem="unsafe")
    unsafe.idempotent = False
    repo.create_job(unsafe)
    repo.claim_next_job(worker_id="w1", workspace_id="ws-1", now=now)
    repo.claim_next_job(worker_id="w2", workspace_id="ws-1", now=now)
    repo.recover_expired_jobs(now=now + timedelta(seconds=11))
    assert repo.get_job("safe", workspace_id="ws-1").status == JobStatus.QUEUED.value
    assert repo.get_job("unsafe", workspace_id="ws-1").status == JobStatus.RECOVERY_REQUIRED.value


def test_production_refuses_jsonl_and_missing_dsn():
    with pytest.raises(JobRepositoryError, match="jsonl_not_allowed"):
        create_job_repository(env={"SECONDBRAIN_ENV": "production", "JOB_REPOSITORY_BACKEND": "jsonl"})
    with pytest.raises(JobRepositoryError, match="requires_database_url"):
        create_job_repository(env={"SECONDBRAIN_ENV": "production"})
