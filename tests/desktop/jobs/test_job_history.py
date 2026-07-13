from secondbrain.desktop.jobs import DesktopJob, JobHistory


def test_history_limits_entries_and_returns_latest():
    history = JobHistory(max_entries=2)
    for name in ["a", "b", "c"]:
        job = DesktopJob(name=name)
        job.mark_completed()
        history.add(job)
    assert [job.name for job in history.entries] == ["b", "c"]
    assert [job.name for job in history.latest(1)] == ["c"]


def test_history_persists_to_disk(tmp_path):
    history = JobHistory()
    job = DesktopJob(name="diagnostics")
    job.mark_completed()
    history.add(job)
    path = tmp_path / "history.json"
    history.save(path)
    loaded = JobHistory.load(path)
    assert loaded.entries[0].name == "diagnostics"
