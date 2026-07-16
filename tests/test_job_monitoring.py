from datetime import datetime, timezone

import pytest

from secondbrain.jobs.models import Job, JobType
from secondbrain.jobs.monitoring import JobMetrics
from secondbrain.jobs.repository import PostgresJobRepository
from secondbrain.jobs.worker import WorkerRegistry
from secondbrain.storage.db_executor import SqliteExecutor


def test_metrics_are_workspace_scoped_and_content_free(tmp_path):
    repo = PostgresJobRepository(SqliteExecutor(str(tmp_path / "metrics.sqlite")))
    repo.ensure_schema()
    repo.create_job(Job(job_id="j", type=JobType.IMPORT.value, workspace_id="ws",
                        payload_reference="secret://must-not-leak", idempotency_key="j",
                        created_at="2026-01-01T00:00:00+00:00"))
    repo.create_job(Job(job_id="other", type=JobType.BACKUP.value, workspace_id="other",
                        payload_reference="payload://other", idempotency_key="other"))
    repo.claim_next_job(worker_id="w1", workspace_id="ws",
                        now=datetime(2026, 1, 1, 0, 0, 10, tzinfo=timezone.utc))
    with pytest.raises(PermissionError):
        repo.renew_lease("j", workspace_id="ws", worker_id="wrong")
    workers = WorkerRegistry()
    workers.heartbeat("w1", active=1)
    metrics = JobMetrics(repo, workers).snapshot(
        workspace_id="ws", now=datetime(2026, 1, 1, 0, 0, 20, tzinfo=timezone.utc))
    assert metrics["average_wait_seconds"] == 10.0
    assert metrics["lease_conflicts"] == 1
    assert metrics["jobs_per_type"] == {JobType.IMPORT.value: 1}
    assert metrics["worker_health"][0]["worker_id"] == "w1"
    assert "secret" not in str(metrics)
