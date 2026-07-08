from __future__ import annotations

from datetime import datetime, timedelta, timezone

from secondbrain.agent.scheduler import JobScheduler

from tests._bg_fakes import FakeJobs


def _sched(tmp_path, **kw):
    return JobScheduler(tmp_path, jobs_service=FakeJobs(), **kw)


def test_register_and_list(tmp_path):
    sch = _sched(tmp_path)
    job = sch.add("nightly", "0 2 * * *", kind="reindex")
    listed = sch.list()
    assert len(listed) == 1
    assert listed[0]["id"] == job.id
    assert listed[0]["schedule"]["cron"] == "0 2 * * *"


def test_interval_job_runs_and_enqueues(tmp_path):
    jobs = FakeJobs()
    sch = JobScheduler(tmp_path, jobs_service=jobs)
    sch.add("ping", {"interval_seconds": 60}, kind="system", job_id="j1")
    runs = sch.run_due(now=datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc))
    assert len(runs) == 1
    assert runs[0].status == "success"
    assert runs[0].queue_job_id                     # mirrored into the Job Queue
    assert len(jobs.jobs) == 1                       # exactly one queue job


def test_job_not_due_again_immediately(tmp_path):
    sch = _sched(tmp_path)
    sch.add("ping", {"interval_seconds": 3600}, job_id="j1")
    t0 = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    assert len(sch.run_due(now=t0)) == 1
    # 10 minutes later -> not due
    assert sch.run_due(now=t0 + timedelta(minutes=10)) == []
    # 61 minutes later -> due again
    assert len(sch.run_due(now=t0 + timedelta(minutes=61))) == 1


def test_disabled_job_not_due(tmp_path):
    sch = _sched(tmp_path)
    job = sch.add("ping", {"interval_seconds": 1}, job_id="j1")
    job.enabled = False
    sch.store.upsert(job)
    assert sch.run_due(now=datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)) == []


def test_runs_recorded_and_counted(tmp_path):
    sch = _sched(tmp_path)
    sch.add("ping", {"interval_seconds": 1}, job_id="j1")
    sch.run_due(now=datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc))
    recorded = sch.runs("j1")
    assert len(recorded) == 1
    assert sch.store.get("j1").run_count == 1
    assert sch.store.get("j1").last_status == "success"


def test_cron_job_fires_on_match(tmp_path):
    sch = _sched(tmp_path)
    sch.add("hourly", "0 * * * *", job_id="h1")
    off = sch.run_due(now=datetime(2026, 7, 6, 12, 30, tzinfo=timezone.utc))
    assert off == []                                 # 12:30 does not match "0 * * * *"
    on = sch.run_due(now=datetime(2026, 7, 6, 13, 0, tzinfo=timezone.utc))
    assert len(on) == 1
