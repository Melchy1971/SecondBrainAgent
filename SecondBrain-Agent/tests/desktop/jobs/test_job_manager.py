import pytest
from secondbrain.desktop.jobs import JobManager, JobState


def test_manager_enqueue_and_run_next():
    events = []
    manager = JobManager(emit=lambda event, payload: events.append(event))
    manager.registry.register("reindex", lambda meta: {"indexed": meta["workspace"]})
    job = manager.enqueue("reindex", {"workspace": "default"})
    result = manager.run_next()
    assert result.job_id == job.job_id
    assert result.state == JobState.COMPLETED
    assert result.metadata["indexed"] == "default"
    assert manager.summary()["queue_length"] == 0
    assert "JOB_COMPLETED" in events


def test_manager_cancels_queued_job():
    manager = JobManager()
    manager.registry.register("sync", lambda meta: None)
    job = manager.enqueue("sync")
    cancelled = manager.cancel(job.job_id)
    assert cancelled.state == JobState.CANCELLED
    assert manager.summary()["active_jobs"] == 0


def test_manager_blocks_non_cancellable_job_cancel():
    manager = JobManager()
    manager.registry.register("upgrade", lambda meta: None, cancellable=False)
    job = manager.enqueue("upgrade")
    with pytest.raises(ValueError):
        manager.cancel(job.job_id)
