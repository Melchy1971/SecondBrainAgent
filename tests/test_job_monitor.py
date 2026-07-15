from secondbrain.jobs.gui import RepositoryJobMonitor, render_jobs_html
from secondbrain.jobs.models import Job, JobStatus, JobType
from secondbrain.jobs.repository import PostgresJobRepository
from secondbrain.storage.db_executor import SqliteExecutor


def test_monitor_is_workspace_scoped_redacted_and_actionable(tmp_path):
    repo = PostgresJobRepository(SqliteExecutor(str(tmp_path / "monitor.sqlite")))
    repo.ensure_schema()
    repo.create_job(Job(job_id="mine", type=JobType.BACKUP.value, workspace_id="ws",
                        payload_reference="secret://payload", idempotency_key="mine",
                        approval_required=True, status=JobStatus.WAITING_FOR_APPROVAL.value))
    repo.create_job(Job(job_id="other", type=JobType.BACKUP.value, workspace_id="other",
                        payload_reference="payload://other", idempotency_key="other"))
    monitor = RepositoryJobMonitor(repo, workspace_id="ws")
    view = monitor.build()
    assert len(view["jobs"]) == 1
    assert "payload_reference" not in view["jobs"][0]
    assert "secret://payload" not in render_jobs_html(view)
    assert monitor.approval_link("mine") == "approval://inbox"
    monitor.cancel("mine")
    assert repo.get_job("mine", workspace_id="ws").status == JobStatus.CANCELLED.value
    assert repo.get_job("other", workspace_id="other").status == JobStatus.QUEUED.value
