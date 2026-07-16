"""Sprint 51 acceptance tests - persistent long-running jobs."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor

import pytest

from secondbrain.jobs.models import Job, JobLease, JobPriority, JobStatus, JobType, priority_rank
from secondbrain.jobs.service import JobStore, JobManager
from secondbrain.jobs.gui import JobMonitorViewModel, render_jobs_html

WS = "ws-1"
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _mgr(tmp_path, lease=60.0):
    store = JobStore(str(tmp_path / "jobs.jsonl"))
    return JobManager(store, lease_seconds=lease)


def test_canonical_model_aliases_and_priorities():
    job = Job(job_id="j", type=JobType.IMPORT.value, workspace_id="ws",
              priority=JobPriority.CRITICAL.value)
    assert job.job_type == JobType.IMPORT.value
    assert isinstance(job.lease, JobLease)
    assert priority_rank(job.priority) > priority_rank(JobPriority.HIGH.value)


class ApprovalAuthority:
    def __init__(self, allowed):
        self.allowed = set(allowed)
        self.claimed = set()

    def claim(self, *, job):
        if job.job_id not in self.allowed or job.job_id in self.claimed:
            return False
        self.claimed.add(job.job_id)
        return True


# 1: job survives restart
def test_job_survives_restart(tmp_path):
    path = str(tmp_path / "jobs.jsonl")
    m1 = JobManager(JobStore(path))
    job = m1.enqueue(type=JobType.REINDEX.value, workspace_id=WS, payload_reference="ref-1", priority=5)
    # fresh store from the same file == restart
    m2 = JobManager(JobStore(path))
    restored = m2.store.get(job.job_id)
    assert restored is not None
    assert restored.payload_reference == "ref-1" and restored.priority == 5


# 2: checkpoint is used
def test_checkpoint_used(tmp_path):
    m = _mgr(tmp_path)
    job = m.enqueue(type=JobType.EMBEDDING.value, workspace_id=WS, payload_reference="ref")
    claimed = m.claim(worker_id="w1", now=T0)
    m.checkpoint(claimed.job_id, "w1", {"offset": 500}, progress=0.5)
    # restart, resume from checkpoint
    m2 = JobManager(JobStore(m.store.path))
    j = m2.store.get(job.job_id)
    assert j.checkpoint == {"offset": 500} and j.progress == 0.5


# 3: crash produces recovery
def test_crash_recovery(tmp_path):
    m = _mgr(tmp_path, lease=10.0)
    job = m.enqueue(type=JobType.REINDEX.value, workspace_id=WS, payload_reference="ref")
    m.claim(worker_id="w1", now=T0)
    # worker dies; lease expires
    recovered = m.recover_stale(now=T0 + timedelta(seconds=30))
    assert job.job_id in recovered
    assert m.store.get(job.job_id).status == JobStatus.QUEUED.value  # requeued for resume


# 4: idempotent job can be continued
def test_idempotent_continues(tmp_path):
    m = _mgr(tmp_path, lease=10.0)
    job = m.enqueue(type=JobType.EMBEDDING.value, workspace_id=WS, payload_reference="ref")
    m.claim(worker_id="w1", now=T0)
    m.checkpoint(job.job_id, "w1", {"offset": 100}, progress=0.3)
    m.recover_stale(now=T0 + timedelta(seconds=30))
    reclaimed = m.claim(worker_id="w2", now=T0 + timedelta(seconds=40))
    assert reclaimed.job_id == job.job_id
    assert reclaimed.checkpoint == {"offset": 100}  # continues, not restarts


# 5: non-idempotent job requires review
def test_non_idempotent_review(tmp_path):
    m = _mgr(tmp_path, lease=10.0)
    job = m.enqueue(type=JobType.RESTORE.value, workspace_id=WS, payload_reference="ref")
    assert job.idempotent is False
    m.claim(worker_id="w1", now=T0)
    # crash -> not auto-requeued, needs review
    m.recover_stale(now=T0 + timedelta(seconds=30))
    assert m.store.get(job.job_id).status == JobStatus.RECOVERY_REQUIRED.value
    # explicit fail also routes to review, never retry
    job2 = m.enqueue(type=JobType.AGENT_PLAN.value, workspace_id=WS, payload_reference="ref2")
    m.claim(worker_id="w1", now=T0)
    res = m.fail(job2.job_id, "w1", "external error", now=T0)
    assert res["status"] == "recovery_required"


# 6: cancel stops controlled
def test_cancel_controlled(tmp_path):
    m = _mgr(tmp_path)
    job = m.enqueue(type=JobType.IMPORT.value, workspace_id=WS, payload_reference="ref")
    m.claim(worker_id="w1", now=T0)
    m.cancel(job.job_id)
    j = m.store.get(job.job_id)
    assert j.status == JobStatus.CANCELLED.value
    assert j.lease.worker_id == ""
    # cancelled job is not dispatched again
    assert m.claim(worker_id="w2", now=T0) is None


# 7: approval state preserved across restart
def test_approval_preserved(tmp_path):
    path = str(tmp_path / "jobs.jsonl")
    m1 = JobManager(JobStore(path))
    job = m1.enqueue(type=JobType.AGENT_PLAN.value, workspace_id=WS, payload_reference="ref",
                     approval_required=True)
    assert job.status == JobStatus.WAITING_FOR_APPROVAL.value
    # restart -> still waiting, not silently runnable
    m2 = JobManager(JobStore(path))
    j = m2.store.get(job.job_id)
    assert j.status == JobStatus.WAITING_FOR_APPROVAL.value and not j.approved
    assert m2.claim(worker_id="w1", now=T0) is None  # not dispatched without approval
    m2.approve(job.job_id, approval_authority=ApprovalAuthority([job.job_id]))
    assert m2.claim(worker_id="w1", now=T0).job_id == job.job_id


# 8: no double execution (exactly-once by idempotency key)
def test_no_double_execution(tmp_path):
    m = _mgr(tmp_path)
    job = m.enqueue(type=JobType.BACKUP.value, workspace_id=WS, payload_reference="ref",
                    idempotency_key="backup-2026-01-01")
    m.claim(worker_id="w1", now=T0)
    assert m.complete(job.job_id, "w1", now=T0)["status"] == "completed"
    assert m.complete(job.job_id, "w1", now=T0)["status"] == "duplicate"
    # a second job with the same idempotency key is also blocked from completing
    job2 = m.enqueue(type=JobType.BACKUP.value, workspace_id=WS, payload_reference="ref",
                     idempotency_key="backup-2026-01-01")
    m.claim(worker_id="w1", now=T0)
    m.store.get(job2.job_id).status = JobStatus.QUEUED.value  # simulate not-yet-running
    assert m.complete(job2.job_id, "w1", now=T0)["status"] == "duplicate"


# 9: queue priority works
def test_queue_priority(tmp_path):
    m = _mgr(tmp_path)
    m.enqueue(type=JobType.IMPORT.value, workspace_id=WS, payload_reference="low", priority=1)
    m.enqueue(type=JobType.IMPORT.value, workspace_id=WS, payload_reference="high", priority=9)
    claimed = m.claim(worker_id="w1", now=T0)
    assert claimed.payload_reference == "high"


# 10: GUI does not block (pure snapshot, no execution)
def test_gui_non_blocking(tmp_path):
    m = _mgr(tmp_path)
    m.enqueue(type=JobType.REINDEX.value, workspace_id=WS, payload_reference="ref", priority=3)
    view = JobMonitorViewModel(m).build(workspace_id=WS)
    assert view["jobs"] and "counts" in view
    html_out = render_jobs_html(view)
    assert "Job Monitor" in html_out


# workspace isolation
def test_workspace_isolation(tmp_path):
    m = _mgr(tmp_path)
    m.enqueue(type=JobType.IMPORT.value, workspace_id=WS, payload_reference="a", priority=5)
    m.enqueue(type=JobType.IMPORT.value, workspace_id="ws-2", payload_reference="b", priority=9)
    claimed = m.claim(worker_id="w1", workspace_id=WS, now=T0)
    assert claimed.payload_reference == "a"  # never picks ws-2's higher-priority job
    assert len(m.store.all(workspace_id=WS)) == 1


# payload only referenced, never stored
def test_payload_reference_only(tmp_path):
    m = _mgr(tmp_path)
    job = m.enqueue(type=JobType.IMPORT.value, workspace_id=WS, payload_reference="s3://bucket/large")
    assert job.payload_reference == "s3://bucket/large"
    assert not hasattr(job, "payload")
    raw = open(m.store.path, encoding="utf-8").read()
    assert '"payload"' not in raw  # only the reference is persisted


# retry with backoff for idempotent
def test_retry_backoff(tmp_path):
    m = _mgr(tmp_path)
    job = m.enqueue(type=JobType.EMBEDDING.value, workspace_id=WS, payload_reference="ref", max_attempts=3)
    m.claim(worker_id="w1", now=T0)
    r = m.fail(job.job_id, "w1", "temporary", now=T0)
    assert r["status"] == "retrying" and r["backoff_seconds"] > 0
    assert m.store.get(job.job_id).status == JobStatus.QUEUED.value


# lease held by other worker rejected
def test_lease_ownership(tmp_path):
    m = _mgr(tmp_path)
    job = m.enqueue(type=JobType.REINDEX.value, workspace_id=WS, payload_reference="ref")
    m.claim(worker_id="w1", now=T0)
    with pytest.raises(PermissionError):
        m.heartbeat(job.job_id, "w2", now=T0)
    with pytest.raises(PermissionError):
        m.complete(job.job_id, "w2", now=T0)


def test_graceful_shutdown_and_metrics(tmp_path):
    manager = _mgr(tmp_path)
    job = manager.enqueue(type=JobType.DIAGNOSTICS.value, workspace_id=WS, payload_reference="ref")
    manager.claim(worker_id="worker", now=T0)
    assert manager.graceful_shutdown("worker") == [job.job_id]
    assert manager.metrics(workspace_id=WS)["queue_length"] == 1


def test_parallel_stores_claim_job_only_once(tmp_path):
    path = str(tmp_path / "jobs.jsonl")
    first = JobManager(JobStore(path))
    first.enqueue(type=JobType.IMPORT.value, workspace_id=WS, payload_reference="ref")
    second = JobManager(JobStore(path))
    with ThreadPoolExecutor(max_workers=2) as pool:
        claimed = list(pool.map(lambda manager: manager.claim(worker_id=str(id(manager)), now=T0), [first, second]))
    assert sum(job is not None for job in claimed) == 1


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
