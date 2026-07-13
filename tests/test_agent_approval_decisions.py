from __future__ import annotations

import json

import pytest

from secondbrain.agent.approval_service import AgentApprovalService
from secondbrain.agent.task_planner import TaskStepState
from secondbrain.native.approval import APPROVAL_SCHEMA, NativeApprovalQueue, approval_path


def _create_approval(queue: NativeApprovalQueue, *, plan_id: str = "plan-1") -> dict:
    return queue.create(
        command="documents.delete",
        intent="delete_document",
        text=f"Delete document for {plan_id}",
        target=f"{plan_id}:step-1",
        plan_id=plan_id,
        step_id="step-1",
        tool_name="documents.delete",
        step_state=TaskStepState.WAITING_FOR_APPROVAL.value,
    )


def _assert_audit(record: dict, old_status: str, new_status: str, actor: str) -> None:
    event = record["decision_audit"][-1]
    assert event == {
        "approval_id": record["approval_id"],
        "old_status": old_status,
        "new_status": new_status,
        "actor": actor,
        "note": record["decision_note"],
        "timestamp": record["decided_at"],
        "plan_id": record.get("plan_id", ""),
        "step_id": record.get("step_id", ""),
        "tool_name": record.get("tool_name") or record["command"],
    }


def test_pending_approval_can_be_approved(tmp_path):
    queue = NativeApprovalQueue(tmp_path)
    created = _create_approval(queue)
    service = AgentApprovalService(queue=queue)

    approved = service.approve(created["approval_id"], "alice", "looks good")

    assert approved["status"] == "approved"
    assert approved["step_state"] == TaskStepState.APPROVED.value
    assert approved["decided_by"] == "alice"
    assert approved["decision_note"] == "looks good"
    assert approved["decided_at"]
    assert service.list_pending() == []
    _assert_audit(approved, "pending", "approved", "alice")


def test_pending_approval_can_be_rejected(tmp_path):
    queue = NativeApprovalQueue(tmp_path)
    created = _create_approval(queue)

    rejected = AgentApprovalService(queue=queue).reject(created["approval_id"], "bob", "too risky")

    assert rejected["status"] == "rejected"
    assert rejected["step_state"] == TaskStepState.REJECTED.value
    _assert_audit(rejected, "pending", "rejected", "bob")


def test_pending_approval_can_be_deferred(tmp_path):
    queue = NativeApprovalQueue(tmp_path)
    created = _create_approval(queue)

    deferred = AgentApprovalService(queue=queue).defer(
        created["approval_id"],
        "carol",
        until="2026-07-15T09:00:00+00:00",
        note="review later",
    )

    assert deferred["status"] == "deferred"
    assert deferred["step_state"] == TaskStepState.DEFERRED.value
    assert deferred["deferred_until"] == "2026-07-15T09:00:00+00:00"
    _assert_audit(deferred, "pending", "deferred", "carol")


def test_deferred_approval_can_later_be_approved(tmp_path):
    queue = NativeApprovalQueue(tmp_path)
    created = _create_approval(queue)
    service = AgentApprovalService(queue=queue)
    service.defer(created["approval_id"], "carol")

    approved = service.approve(created["approval_id"], "alice")

    assert approved["status"] == "approved"
    assert approved["step_state"] == TaskStepState.APPROVED.value
    assert len(approved["decision_audit"]) == 2
    _assert_audit(approved, "deferred", "approved", "alice")


def test_deferred_approval_can_later_be_rejected(tmp_path):
    queue = NativeApprovalQueue(tmp_path)
    created = _create_approval(queue)
    service = AgentApprovalService(queue=queue)
    service.defer(created["approval_id"], "carol")

    rejected = service.reject(created["approval_id"], "bob")

    assert rejected["status"] == "rejected"
    assert rejected["step_state"] == TaskStepState.REJECTED.value
    assert len(rejected["decision_audit"]) == 2
    _assert_audit(rejected, "deferred", "rejected", "bob")


def test_terminal_approval_cannot_be_decided_twice(tmp_path):
    queue = NativeApprovalQueue(tmp_path)
    created = _create_approval(queue)
    service = AgentApprovalService(queue=queue)
    service.approve(created["approval_id"], "alice")

    with pytest.raises(ValueError, match="invalid_approval_transition:approved->approved"):
        service.approve(created["approval_id"], "alice")
    with pytest.raises(ValueError, match="invalid_approval_transition:approved->rejected"):
        service.reject(created["approval_id"], "bob")

    stored = service.get(created["approval_id"])
    assert stored is not None
    assert len(stored["decision_audit"]) == 1

    rejected = _create_approval(queue, plan_id="plan-2")
    service.reject(rejected["approval_id"], "bob")
    with pytest.raises(ValueError, match="invalid_approval_transition:rejected->approved"):
        service.approve(rejected["approval_id"], "alice")


def test_service_get_and_list_by_plan(tmp_path):
    queue = NativeApprovalQueue(tmp_path)
    first = _create_approval(queue, plan_id="plan-1")
    _create_approval(queue, plan_id="plan-2")
    service = AgentApprovalService(queue=queue)

    assert service.get(first["approval_id"])["plan_id"] == "plan-1"
    assert [row["plan_id"] for row in service.list_by_plan("plan-1")] == ["plan-1"]


def test_legacy_approval_without_decision_fields_remains_compatible(tmp_path):
    path = approval_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    legacy = {
        "schema": APPROVAL_SCHEMA,
        "approval_id": "legacy-1",
        "created_at": "2026-01-01T00:00:00+00:00",
        "command": "legacy.write",
        "intent": "legacy",
        "text": "Legacy approval",
        "status": "pending",
    }
    path.write_text(json.dumps(legacy) + "\n", encoding="utf-8")
    service = AgentApprovalService(queue=NativeApprovalQueue(tmp_path))

    loaded = service.get("legacy-1")
    assert loaded is not None
    assert loaded["decision_note"] == ""
    assert loaded["decision_audit"] == []

    approved = service.approve("legacy-1", "migration")
    assert approved["status"] == "approved"
    _assert_audit(approved, "pending", "approved", "migration")
    assert list(path.parent.glob("approval_queue.jsonl.*.tmp")) == []
