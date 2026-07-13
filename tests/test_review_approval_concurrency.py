"""Prompt 14 - concurrency, locking and crash recovery for approvals.

Acceptance coverage:
  1. Two parallel approves lead to only one execution.
  2. Approve and reject at once produce a controlled conflict.
  3. A stale version is rejected.
  4. A tool handler is consumed exactly once.
  5. A process abort leaves a recovery status.
  6. An idempotent tool can be resumed in a controlled way.
  7. Send/delete and other non-idempotent tools require fresh review.
  8. A corrupted main file can be restored from backup.
  9. No record is lost.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Lock
import time

import pytest

from secondbrain.agent.approval_bridge import AgentApprovalBridge
from secondbrain.agent.plan_store import AgentPlanStore, StalePlanError
from secondbrain.agent.safe_executor import SafeExecutor
from secondbrain.agent.task_planner import TaskPlan, TaskStep, TaskStepState
from secondbrain.agent.tool_registry import ToolDefinition, ToolRegistry, ToolRiskLevel
from secondbrain.native.approval import (
    ApprovalConcurrencyError,
    ConflictError,
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
    assert execution["lease_id"] == execution["execution_token"]
    assert execution["owner"] == "worker-1"
    assert execution["acquired_at"]
    assert execution["expires_at"]
    assert execution["heartbeat_at"]
    renewed = queue.heartbeat_execution(approval_id, lease_id=execution["lease_id"])
    assert renewed["version"] == execution["version"] + 1
    with pytest.raises((ApprovalConcurrencyError, ExecutionTokenError)):
        queue.begin_execution(approval_id, executor_id="worker-2")


def test_parallel_resume_executes_handler_exactly_once(tmp_path):
    calls = 0
    calls_lock = Lock()

    def handler(_payload):
        nonlocal calls
        time.sleep(0.05)
        with calls_lock:
            calls += 1
        return {"deleted": True}

    queue = NativeApprovalQueue(tmp_path)
    bridge = AgentApprovalBridge(queue=queue)
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            "records.delete",
            "Delete a record",
            risk_level=ToolRiskLevel.HIGH,
            requires_approval=True,
            handler=handler,
        )
    )
    store = AgentPlanStore(tmp_path, registry=registry)
    executor = SafeExecutor(registry, approval_bridge=bridge, plan_store=store)
    plan = TaskPlan(
        plan_id="parallel-plan",
        intent="delete_record",
        metadata={},
        steps=[TaskStep("step-1", "delete", "records.delete", {})],
    )
    waiting = executor.execute(plan)
    approval_id = waiting.approval_ids[0]
    queue.transition(approval_id, "approved", actor="reviewer")

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: executor.resume_approved(approval_id), range(2)))

    assert calls == 1
    assert {result.status for result in results} <= {"completed", "execution_in_progress"}
    stored = queue.get(approval_id)
    assert stored["status"] == "executed"
    assert stored["consumed_at"]
    assert stored["execution_result_hash"]
    assert stored["lease_id"] == ""


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

    with pytest.raises(ConflictError):
        queue.transition(approval_id, "executing", actor="reviewer", expected_version=0)

    current = queue.get(approval_id)
    assert current["previous_status"] == "pending"
    assert current["updated_at"]


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


def test_idempotent_plan_recovery_runs_handler_once(tmp_path):
    calls = []
    queue = NativeApprovalQueue(tmp_path)
    bridge = AgentApprovalBridge(queue=queue)
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            "data.read",
            "Read data",
            risk_level=ToolRiskLevel.LOW,
            requires_approval=True,
            handler=lambda payload: calls.append(dict(payload)) or {"ok": True},
        )
    )
    store = AgentPlanStore(tmp_path, registry=registry)
    executor = SafeExecutor(registry, approval_bridge=bridge, plan_store=store)
    plan = TaskPlan(
        plan_id="recovery-plan",
        intent="read",
        metadata={},
        steps=[TaskStep("read-step", "read", "data.read", {"query": "safe"})],
    )
    waiting = executor.execute(plan)
    approval_id = waiting.approval_ids[0]
    queue.transition(approval_id, "approved", actor="reviewer")
    queue.begin_execution(approval_id, executor_id="crashed", lease_seconds=1)
    queue.recover_stale_leases(now=datetime.now(timezone.utc) + timedelta(hours=1))

    recovered = executor.resume_after_recovery(approval_id, executor_id="recovery-worker")

    assert recovered["ok"] is True
    assert calls == [{"query": "safe"}]
    assert store.load("recovery-plan").steps[0].state == TaskStepState.COMPLETED
    assert queue.get(approval_id)["consumed_at"]


def test_recovery_finalizes_completed_plan_without_rerunning_handler(tmp_path):
    calls = []
    queue = NativeApprovalQueue(tmp_path)
    bridge = AgentApprovalBridge(queue=queue)
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            "data.read",
            "Read data",
            risk_level=ToolRiskLevel.LOW,
            requires_approval=True,
            handler=lambda payload: calls.append(payload),
        )
    )
    store = AgentPlanStore(tmp_path, registry=registry)
    executor = SafeExecutor(registry, approval_bridge=bridge, plan_store=store)
    plan = TaskPlan(
        plan_id="completed-before-queue",
        intent="read",
        metadata={},
        steps=[TaskStep("read-step", "read", "data.read", {})],
    )
    waiting = executor.execute(plan)
    approval_id = waiting.approval_ids[0]
    queue.transition(approval_id, "approved", actor="reviewer")
    queue.begin_execution(approval_id, executor_id="crashed", lease_seconds=1)
    queue.recover_stale_leases(now=datetime.now(timezone.utc) + timedelta(hours=1))
    persisted = store.load(plan.plan_id)
    persisted.steps[0].state = TaskStepState.COMPLETED
    persisted.metadata["status"] = "completed"
    store.update(persisted)

    result = executor.resume_after_recovery(approval_id)

    assert result["ok"] is True
    assert calls == []
    assert queue.get(approval_id)["status"] == "executed"


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


@pytest.mark.parametrize(
    ("command", "category"),
    (("mail.send", "risky_agent_action"), ("records.delete", "delete_request")),
)
def test_send_and_delete_are_never_automatically_retried(tmp_path, command, category):
    queue = NativeApprovalQueue(tmp_path)
    approval = queue.create(
        command=command,
        intent=command,
        text=command,
        category=category,
        risk_level="low",  # Deliberately misconfigured.
        tool_name=command,
        tool_idempotent=True,
    )
    queue.transition(approval["approval_id"], "approved", actor="reviewer")
    queue.begin_execution(approval["approval_id"], executor_id="crashed", lease_seconds=1)
    queue.recover_stale_leases(now=datetime.now(timezone.utc) + timedelta(hours=1))

    with pytest.raises(ExecutionTokenError, match="manual_review_required"):
        queue.begin_execution(approval["approval_id"], executor_id="recovery")


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
    audit = tmp_path / "runtime" / "native" / "approval_recovery_audit.jsonl"
    assert "backup_restored" in audit.read_text(encoding="utf-8")


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
