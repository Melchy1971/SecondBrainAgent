from pathlib import Path

from secondbrain.native.actions import NativeActionDispatcher
from secondbrain.native.approval import NativeActionAuditLog, NativeApprovalQueue, native_audit_status
from secondbrain.native.runtime_snapshot import build_native_view_model


def test_every_native_action_writes_audit_record(tmp_path: Path):
    dispatcher = NativeActionDispatcher(tmp_path)
    result = dispatcher.parse_and_dispatch("Öffne Dokumente")
    assert result.ok is True
    audit = NativeActionAuditLog(tmp_path).latest()
    assert audit
    assert audit[0]["command"] == "native-open:documents"
    assert audit[0]["status"] == "navigated"


def test_mutating_action_creates_pending_approval(tmp_path: Path):
    dispatcher = NativeActionDispatcher(tmp_path)
    result = dispatcher.parse_and_dispatch("Repariere Index")
    assert result.ok is False
    assert result.status == "confirmation_required"
    approvals = NativeApprovalQueue(tmp_path).list(status="pending")
    assert len(approvals) == 1
    assert approvals[0]["command"] == "p1-vector-index-repair"
    assert approvals[0]["status"] == "pending"


def test_approval_queue_can_mark_rejected(tmp_path: Path):
    queue = NativeApprovalQueue(tmp_path)
    created = queue.create(command="memory-note", intent="remember", text="Merke Test", target="memory")
    updated = queue.mark(created["approval_id"], "rejected")
    assert updated is not None
    assert updated["status"] == "rejected"
    assert queue.list(status="pending") == []


def test_native_audit_status_exposes_pending_approvals(tmp_path: Path):
    dispatcher = NativeActionDispatcher(tmp_path)
    dispatcher.parse_and_dispatch("Repariere Index")
    status = native_audit_status(tmp_path)
    assert status["schema"] == "secondbrain.native.audit_status.v30_28"
    assert status["pending_approvals"] == 1
    assert status["latest"]


def test_native_view_model_exposes_v3028_audit_surface(tmp_path: Path):
    model = build_native_view_model(tmp_path)
    assert model["schema"] == "secondbrain.native.view_model.v30_28"
    assert model["version"] == "30.28"
    assert model["actions"]["schema"] == "secondbrain.native.actions.v30_28"
    assert "audit" in model
