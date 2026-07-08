from __future__ import annotations

from datetime import timedelta

from secondbrain.agent.safety import ActionGuard, SafetyPolicy, SafetyService
from secondbrain.agent.safety.guard import _utc_now
from secondbrain.native.approval import NativeApprovalQueue, approval_path


def test_guard_allows_read_without_approval(tmp_path):
    guard = ActionGuard(tmp_path)
    decision = guard.guard(actor="agent", action="file.read", text="open note")
    assert decision.allowed is True
    assert decision.outcome == "allow"
    assert decision.approval_id is None
    # no approval written for an auto-allowed action
    assert NativeApprovalQueue(tmp_path).list() == []


def test_guard_requires_approval_and_reuses_native_queue(tmp_path):
    guard = ActionGuard(tmp_path)
    decision = guard.guard(actor="agent", action="file.delete", text="rm note", target="plan:1")
    assert decision.allowed is False
    assert decision.outcome == "require_approval"
    assert decision.risk_level == "destructive"
    assert decision.approval_id

    # The approval must live in the ONE canonical queue file - no second queue.
    queue_file = approval_path(tmp_path)
    assert queue_file.exists()
    assert queue_file == tmp_path.resolve() / "runtime" / "native" / "approval_queue.jsonl"
    rows = NativeApprovalQueue(tmp_path).list()
    assert len(rows) == 1
    assert rows[0]["approval_id"] == decision.approval_id
    assert rows[0]["risk_level"] == "destructive"
    assert rows[0]["status"] == "pending"


def test_guard_deduplicates_pending_approval_for_same_target(tmp_path):
    guard = ActionGuard(tmp_path)
    first = guard.guard(actor="agent", action="db.migrate", target="job:9")
    second = guard.guard(actor="agent", action="db.migrate", target="job:9")
    assert first.approval_id == second.approval_id
    assert len(NativeApprovalQueue(tmp_path).list()) == 1


def test_guard_blocks_configured_action(tmp_path):
    policy = SafetyPolicy.from_config({"blocked_actions": ["shell.exec"]})
    guard = ActionGuard(tmp_path, policy=policy)
    decision = guard.guard(actor="agent", action="shell.exec", text="rm -rf")
    assert decision.outcome == "block"
    assert decision.allowed is False
    assert NativeApprovalQueue(tmp_path).list() == []


def test_service_approve_and_reject_update_same_queue(tmp_path):
    service = SafetyService(tmp_path)
    rec_a = service.request(actor="agent", action="email.send", text="mail A")
    rec_b = service.request(actor="agent", action="file.write", text="write B")

    approved = service.approve(rec_a["approval_id"], decided_by="markus")
    rejected = service.reject(rec_b["approval_id"], decided_by="markus")

    assert approved.ok and approved.status == "approved"
    assert rejected.ok and rejected.status == "rejected"
    assert service.get(rec_a["approval_id"])["status"] == "approved"
    assert service.get(rec_b["approval_id"])["status"] == "rejected"
    assert len(service.list()) == 2  # still one queue, two records


def test_service_decision_not_found(tmp_path):
    service = SafetyService(tmp_path)
    decision = service.approve("does-not-exist")
    assert decision.ok is False
    assert decision.status == "not_found"


def test_expire_marks_only_stale_pending(tmp_path):
    service = SafetyService(tmp_path, ttl_seconds=3600)
    stale = service.request(actor="agent", action="file.delete", text="old", target="t1")
    fresh = service.request(actor="agent", action="file.delete", text="new", target="t2")

    # expire relative to a point 2 hours after creation
    future = _utc_now() + timedelta(hours=2)
    # make the fresh one look recent by expiring with a large TTL for it:
    decisions = service.expire(ttl_seconds=3600, now=future)

    expired_ids = {d.approval_id for d in decisions}
    assert stale["approval_id"] in expired_ids
    assert fresh["approval_id"] in expired_ids  # both are >1h old at `future`

    # with a TTL longer than the age, nothing expires
    service2 = SafetyService(tmp_path)
    none = service2.expire(ttl_seconds=10_000, now=future)
    assert none == []


def test_expire_respects_ttl_boundary(tmp_path):
    service = SafetyService(tmp_path, ttl_seconds=60)
    rec = service.request(actor="agent", action="index.repair", text="repair")
    just_before = _utc_now() + timedelta(seconds=30)
    assert service.expire(now=just_before) == []
    assert service.get(rec["approval_id"])["status"] == "pending"

    well_after = _utc_now() + timedelta(seconds=120)
    decisions = service.expire(now=well_after)
    assert len(decisions) == 1
    assert service.get(rec["approval_id"])["status"] == "expired"
