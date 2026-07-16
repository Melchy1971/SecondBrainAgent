from secondbrain.jobs.models import Job, JobStatus, JobType
from secondbrain.jobs.repository import PostgresJobRepository
from secondbrain.jobs.worker import JobHandlerRegistry, JobWorker, WorkerRegistry
from secondbrain.storage.db_executor import SqliteExecutor


def _runtime(tmp_path, handler, *, idempotent=True, max_attempts=3):
    repo = PostgresJobRepository(SqliteExecutor(str(tmp_path / "worker.sqlite")))
    repo.ensure_schema()
    job = Job(job_id="j1", type=JobType.IMPORT.value, workspace_id="ws",
              payload_reference="payload://j1", idempotency_key="one",
              idempotent=idempotent, max_attempts=max_attempts)
    repo.create_job(job)
    handlers = JobHandlerRegistry()
    handlers.register(JobType.IMPORT.value, handler)
    return repo, JobWorker(repo, handlers, worker_id="w1", workspace_id="ws")


def test_worker_checkpoints_and_completes(tmp_path):
    def handler(job, context):
        context.heartbeat()
        context.checkpoint({"offset": 10}, progress=0.5)

    repo, worker = _runtime(tmp_path, handler)
    result = worker.run_once()
    assert result.status == JobStatus.COMPLETED.value
    assert result.checkpoint == {"offset": 10}
    assert repo.get_job("j1", workspace_id="ws").progress == 1.0


def test_idempotent_failure_retries_but_non_idempotent_requires_recovery(tmp_path):
    def fail(job, context):
        raise RuntimeError("sensitive payload must not appear")

    _, safe_worker = _runtime(tmp_path / "safe", fail)
    assert safe_worker.run_once().status == JobStatus.QUEUED.value
    repo, unsafe_worker = _runtime(tmp_path / "unsafe", fail, idempotent=False)
    result = unsafe_worker.run_once()
    assert result.status == JobStatus.RECOVERY_REQUIRED.value
    assert "sensitive payload" not in result.error_summary
    assert repo.get_job("j1", workspace_id="ws").attempts == 1


def test_registry_and_graceful_shutdown(tmp_path):
    repo, worker = _runtime(tmp_path, lambda job, context: None)
    registry = WorkerRegistry()
    worker.registry = registry
    worker.run_once()
    assert registry.snapshot()[0]["active"] == 0
    worker.shutdown()
    assert registry.snapshot() == []
    assert repo.get_job("j1", workspace_id="ws").status == JobStatus.COMPLETED.value
