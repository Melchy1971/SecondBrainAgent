from __future__ import annotations

from datetime import datetime, timezone

from secondbrain.agent.scheduler import JobScheduler

from tests._bg_fakes import FakeJobs

NOW = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)


def _sched(tmp_path, **kw):
    return JobScheduler(tmp_path, jobs_service=FakeJobs(), **kw)


def test_dependency_runs_after_prerequisite(tmp_path):
    sch = _sched(tmp_path)
    sch.add("a", {"interval_seconds": 1}, job_id="a")
    sch.add("b", {"interval_seconds": 1}, job_id="b", dependencies=["a"])
    runs = sch.run_due(now=NOW)
    order = [r.name for r in runs]
    assert order.index("a") < order.index("b")
    assert all(r.status == "success" for r in runs)


def test_dependent_skipped_when_prerequisite_fails(tmp_path):
    def boom(scheduler, job):
        raise RuntimeError("a_failed")

    sch = _sched(tmp_path, handlers={"a": boom})
    sch.add("a", {"interval_seconds": 1}, job_id="a")
    sch.add("b", {"interval_seconds": 1}, job_id="b", dependencies=["a"])
    runs = {r.name: r for r in sch.run_due(now=NOW)}
    assert runs["a"].status == "failed"
    assert runs["b"].status == "skipped"
    assert "dependency_not_satisfied:a" in runs["b"].error


def test_unknown_dependency_is_ignored(tmp_path):
    sch = _sched(tmp_path)
    sch.add("b", {"interval_seconds": 1}, job_id="b", dependencies=["ghost"])
    runs = sch.run_due(now=NOW)
    assert runs[0].status == "success"


def test_non_due_dependency_with_prior_success_allows_dependent(tmp_path):
    sch = _sched(tmp_path)
    # a runs on a long interval and already succeeded; b depends on a
    a = sch.add("a", {"interval_seconds": 100000}, job_id="a")
    a.last_status = "success"
    a.last_run_at = NOW.isoformat()
    sch.store.upsert(a)
    sch.add("b", {"interval_seconds": 1}, job_id="b", dependencies=["a"])
    runs = {r.name: r for r in sch.run_due(now=NOW)}
    assert "a" not in runs                 # a not due
    assert runs["b"].status == "success"   # dependency satisfied by prior success
