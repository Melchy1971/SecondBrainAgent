from secondbrain.desktop.jobs import DesktopJob, JobRegistry, JobRunner, JobState


def test_runner_completes_job_and_merges_result_metadata():
    events = []
    registry = JobRegistry()
    registry.register("backup", lambda meta: {"backup_id": "b1"})
    job = DesktopJob(name="backup")
    runner = JobRunner(registry, emit=lambda event, payload: events.append(event))
    result = runner.run(job)
    assert result.state == JobState.COMPLETED
    assert result.metadata["backup_id"] == "b1"
    assert events == ["JOB_STARTED", "JOB_COMPLETED"]


def test_runner_fails_job_on_exception():
    registry = JobRegistry()
    def broken(meta):
        raise RuntimeError("boom")
    registry.register("broken", broken)
    job = DesktopJob(name="broken")
    result = JobRunner(registry).run(job)
    assert result.state == JobState.FAILED
    assert result.error == "boom"
