from secondbrain.desktop.connectors.jobs import (
    ConnectorJobHistory,
    ConnectorJobRunner,
    ConnectorJobService,
    ConnectorJobState,
)


def test_connector_job_lifecycle_completes_with_cursor():
    runner = ConnectorJobRunner(lambda connector_id, cursor: {"items_processed": 3, "cursor_after": "c2"})
    service = ConnectorJobService(runner=runner)

    job = service.create_sync_job("gmail", cursor_before="c1")
    result = service.run(job.job_id)

    assert result.accepted is True
    assert result.job.state == ConnectorJobState.COMPLETED
    assert result.job.items_processed == 3
    assert result.job.cursor_before == "c1"
    assert result.job.cursor_after == "c2"


def test_connector_job_failure_is_captured_in_history_and_snapshot():
    def boom(connector_id, cursor):
        raise RuntimeError("api unavailable")

    service = ConnectorJobService(runner=ConnectorJobRunner(boom))
    job = service.create_sync_job("drive")

    result = service.run(job.job_id)
    snapshot = service.snapshot(connector_id="drive")

    assert result.accepted is False
    assert result.job.state == ConnectorJobState.FAILED
    assert snapshot.failed_jobs == 1
    assert snapshot.last_error == "api unavailable"


def test_active_job_snapshot_counts_queued_jobs_as_total_not_running():
    service = ConnectorJobService()
    service.create_sync_job("notion")

    snapshot = service.snapshot()

    assert snapshot.total_jobs == 1
    assert snapshot.running_jobs == 0
    assert snapshot.completed_jobs == 0


def test_cancel_active_connector_job_moves_to_history():
    service = ConnectorJobService()
    job = service.create_sync_job("slack")

    cancelled = service.cancel(job.job_id, "user cancelled")
    snapshot = service.snapshot()

    assert cancelled.state == ConnectorJobState.CANCELLED
    assert snapshot.cancelled_jobs == 1
    assert service.active_jobs() == []


def test_history_filters_by_connector():
    history = ConnectorJobHistory()
    service = ConnectorJobService(history=history)
    gmail = service.create_sync_job("gmail")
    drive = service.create_sync_job("drive")
    service.run(gmail.job_id)
    service.run(drive.job_id)

    assert len(history.list(connector_id="gmail")) == 1
    assert history.last_for("drive").connector_id == "drive"
