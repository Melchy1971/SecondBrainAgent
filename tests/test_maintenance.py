from __future__ import annotations

from datetime import datetime, timezone

from secondbrain.agent.scheduler import JobScheduler, maintenance_jobs

from tests._bg_fakes import FakeJobs


def test_maintenance_jobs_defined():
    names = {j.name for j in maintenance_jobs()}
    assert names == {"health_check", "auto_index", "knowledge_refresh", "memory_consolidation"}


def test_register_maintenance(tmp_path):
    sch = JobScheduler(tmp_path, jobs_service=FakeJobs())
    registered = sch.register_maintenance()
    assert len(registered) == 4
    assert len(sch.list()) == 4


def test_health_check_reads_queue_snapshot(tmp_path):
    jobs = FakeJobs(snapshot_health="ok")
    sch = JobScheduler(tmp_path, jobs_service=jobs)
    sch.register_maintenance()
    # 00:00 fires health_check (*/15) and auto_index (hourly)
    runs = {r.name: r for r in sch.run_due(now=datetime(2026, 7, 6, 0, 0, tzinfo=timezone.utc))}
    assert runs["health_check"].status == "success"
    assert runs["health_check"].output["queue_health"] == "ok"


def test_memory_consolidation_uses_sink(tmp_path):
    facts = []
    sch = JobScheduler(tmp_path, jobs_service=FakeJobs(), memory_sink=lambda f: facts.append(f))
    sch.register_maintenance()
    # 04:00 fires memory_consolidation (0 4 * * *)
    runs = {r.name: r for r in sch.run_due(now=datetime(2026, 7, 6, 4, 0, tzinfo=timezone.utc))}
    assert "memory_consolidation" in runs
    assert runs["memory_consolidation"].output["memory_delivered"] is True
    assert any(f["kind"] == "memory_consolidation" for f in facts)


def test_knowledge_refresh_runs_after_auto_index(tmp_path):
    sch = JobScheduler(tmp_path, jobs_service=FakeJobs())
    sch.register_maintenance()
    # 03:00 fires health_check + auto_index + knowledge_refresh (depends auto_index)
    runs = sch.run_due(now=datetime(2026, 7, 6, 3, 0, tzinfo=timezone.utc))
    names = [r.name for r in runs]
    assert "knowledge_refresh" in names and "auto_index" in names
    assert names.index("auto_index") < names.index("knowledge_refresh")
    assert {r.name: r.status for r in runs}["knowledge_refresh"] == "success"


def test_maintenance_firings_mirrored_into_job_queue(tmp_path):
    jobs = FakeJobs()
    sch = JobScheduler(tmp_path, jobs_service=jobs)
    sch.register_maintenance()
    sch.run_due(now=datetime(2026, 7, 6, 3, 0, tzinfo=timezone.utc))
    # each fired maintenance job enqueued exactly one queue job
    assert len(jobs.jobs) == 3
