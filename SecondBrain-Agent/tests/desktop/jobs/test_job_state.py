from secondbrain.desktop.jobs import DesktopJob, JobState


def test_job_lifecycle_success():
    job = DesktopJob(name="import")
    assert job.state == JobState.CREATED
    job.mark_queued()
    job.mark_running()
    job.mark_progress(50)
    job.mark_completed()
    assert job.state == JobState.COMPLETED
    assert job.progress == 100
    assert job.finished_at is not None


def test_job_serialization_roundtrip():
    job = DesktopJob(name="sync", metadata={"connector": "drive"})
    restored = DesktopJob.from_dict(job.to_dict())
    assert restored.name == "sync"
    assert restored.metadata["connector"] == "drive"
