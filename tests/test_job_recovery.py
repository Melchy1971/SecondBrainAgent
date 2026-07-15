from datetime import datetime, timedelta, timezone

from secondbrain.jobs.models import Job, JobStatus, JobType
from secondbrain.jobs.repository import PostgresJobRepository
from secondbrain.storage.db_executor import SqliteExecutor


def test_restart_recovers_checkpoint_without_duplicate_execution(tmp_path):
    path = str(tmp_path / "restart.sqlite")
    first = PostgresJobRepository(SqliteExecutor(path), lease_seconds=5)
    first.ensure_schema()
    first.create_job(Job(job_id="j", type=JobType.REINDEX.value, workspace_id="ws",
                         payload_reference="payload://j", idempotency_key="unique"))
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    first.claim_next_job(worker_id="dead", workspace_id="ws", now=now)
    first.save_checkpoint("j", workspace_id="ws", worker_id="dead", checkpoint={"page": 7})

    restarted = PostgresJobRepository(SqliteExecutor(path), lease_seconds=5)
    assert restarted.recover_expired_jobs(now=now + timedelta(seconds=6)) == ["j"]
    resumed = restarted.claim_next_job(worker_id="new", workspace_id="ws", now=now + timedelta(seconds=7))
    assert resumed.checkpoint == {"page": 7}
    assert restarted.claim_next_job(worker_id="other", workspace_id="ws") is None
    assert resumed.status == JobStatus.CLAIMED.value
