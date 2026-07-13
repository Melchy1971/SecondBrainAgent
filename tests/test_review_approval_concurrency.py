"""Prompt 14 - concurrency, locking and crash recovery for approvals.

Acceptance coverage:
  1. Two parallel approves lead to only one execution.
  2. Approve and reject at once produce a controlled conflict.
  3. A stale version is rejected.
  4. A process abort leaves a recovery status.
  5. An idempotent tool can be resumed in a controlled way.
  6. A non-idempotent tool requires a fresh review.
  7. A corrupted main file can be restored from backup.
  8. No record is lost.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest

from secondbrain.agent.approval_bridge import AgentApprovalBridge
from secondbrain.agent.plan_store import AgentPlanStore, StalePlanError
from secondbrain.agent.safe_executor import SafeExecutor
from secondbrain.agent.task_planner import TaskPlan, TaskStep, TaskStepState
from secondbrain.agent.tool_registry import ToolRegistry
from secondbrain.native.approval import (
    ApprovalConcurrencyError,
    ExecutionTokenError,
    NativeApprovalQueue,
    approval_path,
)

NOW = datetime(2026, 7, 13, 12, 0, 0, tzinfo=timezone.utc)


def _delete_approval(queue):
    return queue.create(
        command="records.delete",
        intent="delete_record",
        text="Delete 1",
        category="delete_request",
        risk_level="high",
        tool_name="records.delete",
    )


def _read_approval(queue):
    return queue.create(
        command="data.read",
        intent="read",
        text="Read report",
        category="risky_agent_action",
        risk_level="low",
        tool_name="data.read",
    )


# -- 1 ---------------------------------------------------------------------

def test_two_parallel_approves_yield_single_execution(tmp_path):
    queue = NativeApprovalQueue(tmp_path)
    approval_id = _delete_approval(queue)["approval_id"]

    def approve(_):
        try:
            queue.transition(approval_id, "approved", actor="reviewer", expected_version=0)
            return True
        except (ApprovalConcurrencyError, ValueError):
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(approve, range(2)))

    assert sum(outcomes) == 1
    assert queue.get(approval_id)["status"] == "approved"
    assert queue.get(approval_id)["version"] == 1

    execution = queue.begin_execution(approval_id, executor_id="worker-1")
    assert execution["execution_token"]
    with pytest.raises((ApprovalConcurrencyError, ExecutionTokenError)):
        queue.begin_execution(approval_id, executor_id="worker-2")


# -- 2 ---------------------------------------------------------------------

def test_parallel_approve_and_reject_conflict(tmp_path):
    queue = NativeApprovalQueue(tmp_path)
    approval_id = _delete_approval(queue)["approval_id"]

    def decide(action):
        try:
            queue.transition(approval_id, action, actor="reviewer", expected_version=0)
            return f"{action}:ok"
        except (ApprovalConcurrencyError, ValueError) as exc:
            return f"{action}:conflict:{type(exc).__name__}"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = sorted(pool.map(decide, ("approved", "rejected")))

    accepted = [item for item in outcomes if item.endswith(":ok")]
    conflicts = [item for item in outcomes if ":conflict:" in item]
    assert len(accepted) == 1
    assert len(conflicts) == 1


# -- 3 ---------------------------------------------------------------------

def test_stale_version_is_rejected(tmp_path):
    queue = NativeApprovalQueue(tmp_path)
    approval_id = _delete_approval(queue)["approval_id"]
    queue.transition(approval_id, "approved", actor="reviewer")  # version 0 -> 1

    with pytest.raises(ApprovalConcurrencyError):
        queue.transition(approval_id, "executing", actor="reviewer", expected_version=0)


def test_stale_plan_write_is_rejected(tmp_path):
    store = AgentPlanStore(tmp_path)
    plan = TaskPlan(plan_id="p1", intent="demo", metadata={}, steps=[TaskStep(step_id="s1", name="s", tool_name=None, payload={})])
    store.save(plan)  # version 1
    store.update(plan)  # version 2

    with pytest.raises(StalePlanError):
        store.update(plan, expected_version=1)


# -- 4 ---------------------------------------------------------------------

def test_process_abort_leaves_recovery_status(tmp_path):
    queue = NativeApprovalQueue(tmp_path)
    approval_id = _delete_approval(queue)["approval_id"]
    queue.transition(approval_id, "approved", actor="reviewer")
    queue.begin_execution(approval_id, executor_id="worker-1", lease_seconds=1)

    recovered = queue.recover_stale_leases(now=datetime.now(timezone.utc) + timedelta(hours=1))

    assert [row["status"] for row in recovered] == ["recovery_required"]
    assert queue.get(approval_id)["status"] == "recovery_required"
    assert queue.get(approval_id)["execution_token"] == ""


# -- 5 ---------------------------------------------------------------------

def test_idempotent_tool_can_be_resumed(tmp_path):
    queue = NativeApprovalQueue(tmp_path)
    bridge = AgentApprovalBridge(queue=queue)
    executor = SafeExecutor(ToolRegistry(), approval_bridge=bridge, plan_store=AgentPlanStore(tmp_path))
    approval_id = _read_approval(queue)["approval_id"]
    queue.transition(approval_id, "approved", actor="reviewer")
    queue.begin_execution(approval_id, executor_id="worker-1", lease_seconds=1)
    queue.recover_stale_leases(now=datetime.now(timezone.utc) + timedelta(hours=1))

    result = executor.resume_after_recovery(approval_id, executor_id="worker-2")

    assert result["ok"] is True
    assert queue.get(approval_id)["status"] == "completed"


# -- 6 ---------------------------------------------------------------------

def test_non_idempotent_tool_requires_review(tmp_path):
    queue = NativeApprovalQueue(tmp_path)
    bridge = AgentApprovalBridge(queue=queue)
    executor = SafeExecutor(ToolRegistry(), approval_bridge=bridge, plan_store=AgentPlanStore(tmp_path))
    approval_id = _delete_approval(queue)["approval_id"]
    queue.transition(approval_id, "approved", actor="reviewer")
    queue.begin_execution(approval_id, executor_id="worker-1", lease_seconds=1)
    queue.recover_stale_leases(now=datetime.now(timezone.utc) + timedelta(hours=1))

    result = executor.resume_after_recovery(approval_id, executor_id="worker-2")

    assert result["ok"] is False
    assert result["status"] == "manual_review_required"
    # A direct execution attempt is also refused.
    with pytest.raises(ExecutionTokenError):
        queue.begin_execution(approval_id, executor_id="worker-2")


# -- 7 ---------------------------------------------------------------------

def test_corrupted_main_file_restored_from_backup(tmp_path):
    queue = NativeApprovalQueue(tmp_path)
    approval_id = _delete_approval(queue)["approval_id"]
    queue.transition(approval_id, "approved", actor="reviewer")  # writes a .bak of the pre-decision state

    path = approval_path(tmp_path)
    path.write_text("total garbage not json\n", encoding="utf-8")

    rows = queue.get(approval_id)
    assert rows is not None
    assert rows["approval_id"] == approval_id


# -- 8 ---------------------------------------------------------------------

def test_no_record_is_lost_across_operations(tmp_path):
    queue = NativeApprovalQueue(tmp_path)
    ids = [
        _delete_approval(queue)["approval_id"],
        _read_approval(queue)["approval_id"],
        _delete_approval(queue)["approval_id"],
    ]
    queue.transition(ids[0], "approved", actor="reviewer")
    queue.transition(ids[1], "rejected", actor="reviewer")

    # Corrupt then rely on backup restore.
    approval_path(tmp_path).write_text("broken\n", encoding="utf-8")

    stored = {row["approval_id"] for row in queue.list()}
    assert stored == set(ids)


def test_lease_still_valid_is_not_recovered(tmp_path):
    queue = NativeApprovalQueue(tmp_path)
    approval_id = _read_approval(queue)["approval_id"]
    queue.transition(approval_id, "approved", actor="reviewer")
    queue.begin_execution(approval_id, executor_id="worker-1", lease_seconds=3600)

    recovered = queue.recover_stale_leases(now=datetime.now(timezone.utc) + timedelta(minutes=1))

    assert recovered == []
    assert queue.get(approval_id)["status"] == "executing"
