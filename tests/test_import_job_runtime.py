from dataclasses import dataclass

from secondbrain.jobs.integrations import register_import_handler, submit_import_job
from secondbrain.jobs.models import JobStatus
from secondbrain.jobs.repository import PostgresJobRepository
from secondbrain.jobs.worker import JobHandlerRegistry, JobWorker
from secondbrain.storage.db_executor import SqliteExecutor


@dataclass
class Progress:
    session_id: str = "session-1"
    position: int = 8
    percent: float = 50.0


class ImportPipeline:
    def import_file(self, path, *, workspace_id, progress, **options):
        assert path == "inbox/document.md" and workspace_id == "ws"
        progress(Progress())
        return Progress(percent=100.0)


def test_existing_import_pipeline_runs_through_central_runtime(tmp_path):
    repo = PostgresJobRepository(SqliteExecutor(str(tmp_path / "import.sqlite")))
    repo.ensure_schema()
    submit_import_job(repo, workspace_id="ws", payload_reference="import://one", idempotency_key="one")
    handlers = JobHandlerRegistry()
    register_import_handler(handlers, lambda ref: (ImportPipeline(), "inbox/document.md", {}))
    result = JobWorker(repo, handlers, worker_id="import-1", workspace_id="ws").run_once()
    assert result.status == JobStatus.COMPLETED.value
    assert result.checkpoint == {"session_id": "session-1", "position": 8}
