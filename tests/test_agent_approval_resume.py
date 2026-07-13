from __future__ import annotations

import json

import pytest

from secondbrain.agent.agent_core import AgentCore, AgentRequest
from secondbrain.agent.approval_bridge import AgentApprovalBridge
from secondbrain.agent.intent_router import IntentRoute, IntentRouter
from secondbrain.agent.plan_store import AgentPlanStore
from secondbrain.agent.task_planner import TaskPlan, TaskStep, TaskStepState
from secondbrain.agent.tool_registry import ToolDefinition, ToolInputSchema, ToolRegistry, ToolRiskLevel
from secondbrain.native.approval import NativeApprovalQueue


def _agent(tmp_path, handler):
    queue = NativeApprovalQueue(tmp_path)
    bridge = AgentApprovalBridge(queue=queue)
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            "documents.delete",
            "Delete a document",
            input_schema=ToolInputSchema(
                properties={
                    "document_id": {"type": "string"},
                    "token": {"type": "string", "sensitive": True},
                },
                required=("document_id", "token"),
                additional_properties=False,
            ),
            risk_level=ToolRiskLevel.HIGH,
            requires_approval=True,
            handler=handler,
        )
    )
    router = IntentRouter()
    router.add_keyword_rule(
        "delete",
        IntentRoute(
            intent="delete_document",
            tool_name="documents.delete",
            parameters={"document_id": "doc-1", "token": "secret-value"},
        ),
    )
    return AgentCore(
        router=router,
        registry=registry,
        approval_bridge=bridge,
        project_root=tmp_path,
    )


def test_risky_plan_is_persisted_with_sanitized_payload(tmp_path):
    agent = _agent(tmp_path, lambda payload: payload)

    response = agent.handle(AgentRequest(text="delete document"))

    assert response.status == "waiting_for_approval"
    stored = agent.plan_store.load(response.plan.plan_id)
    assert stored.steps[0].state == TaskStepState.WAITING_FOR_APPROVAL
    assert [plan.plan_id for plan in agent.plan_store.list_waiting()] == [response.plan.plan_id]

    path = tmp_path / "runtime" / "agent" / "plans" / f"{response.plan.plan_id}.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["plan_id"] == response.plan.plan_id
    assert record["approval_ids"] == response.approval_ids
    assert record["steps"][0]["payload"] == {"document_id": "doc-1", "token": "***"}
    assert record["created_at"]
    assert record["updated_at"]


def test_approve_resumes_once_and_completes_step(tmp_path):
    calls: list[dict] = []
    agent = _agent(tmp_path, lambda payload: calls.append(dict(payload)) or {"deleted": payload["document_id"]})
    waiting = agent.handle(AgentRequest(text="delete document"))
    approval_id = waiting.approval_ids[0]
    agent.approval_service.approve(approval_id, "reviewer")

    assert agent.plan_store.claim_step(waiting.plan.plan_id, waiting.plan.steps[0].step_id) is True
    concurrent = agent.resume_approval(approval_id)
    assert concurrent.status == "execution_in_progress"
    assert calls == []
    agent.plan_store.release_step(waiting.plan.plan_id, waiting.plan.steps[0].step_id)
    resumed = agent.resume_approval(approval_id)
    repeated = agent.resume_approval(approval_id)

    assert resumed.ok is True
    assert resumed.status == "completed"
    assert resumed.plan.steps[0].state == TaskStepState.COMPLETED
    assert calls == [{"document_id": "doc-1", "token": "secret-value"}]
    assert repeated.status == "completed"
    assert repeated.results == []
    assert repeated.approval_ids == []
    assert len(calls) == 1
    assert agent.approval_service.get(approval_id)["status"] == "executed"


def test_reject_stops_plan_without_executing_tool(tmp_path):
    calls = []
    agent = _agent(tmp_path, lambda payload: calls.append(payload))
    waiting = agent.handle(AgentRequest(text="delete document"))
    approval_id = waiting.approval_ids[0]

    rejected = agent.reject_approval(approval_id)

    assert rejected.status == "rejected"
    assert rejected.errors == []
    assert rejected.plan.metadata["status"] == "rejected"
    assert rejected.plan.steps[0].state == TaskStepState.REJECTED
    assert calls == []
    with pytest.raises(PermissionError, match="approval_not_approved"):
        agent.resume_approval(approval_id)


def test_defer_keeps_plan_paused(tmp_path):
    calls = []
    agent = _agent(tmp_path, lambda payload: calls.append(payload))
    waiting = agent.handle(AgentRequest(text="delete document"))
    approval_id = waiting.approval_ids[0]

    deferred = agent.defer_approval(approval_id, "2026-07-15T09:00:00+00:00")

    assert deferred.status == "waiting_for_approval"
    assert deferred.plan.steps[0].state == TaskStepState.DEFERRED
    assert deferred.plan.metadata["status"] == "waiting_for_approval"
    assert calls == []
    with pytest.raises(PermissionError, match="approval_not_approved"):
        agent.resume_approval(approval_id)


def test_multistep_plan_continues_until_next_approval(tmp_path):
    calls: list[str] = []
    queue = NativeApprovalQueue(tmp_path)
    bridge = AgentApprovalBridge(queue=queue)
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            "risk.first",
            "First risky action",
            requires_approval=True,
            risk_level=ToolRiskLevel.HIGH,
            handler=lambda payload: calls.append("first") or "first-result",
        )
    )
    registry.register(
        ToolDefinition(
            "safe.middle",
            "Safe middle action",
            handler=lambda payload: calls.append("middle") or "middle-result",
        )
    )
    registry.register(
        ToolDefinition(
            "risk.last",
            "Last risky action",
            requires_approval=True,
            risk_level=ToolRiskLevel.HIGH,
            handler=lambda payload: calls.append("last") or "last-result",
        )
    )
    agent = AgentCore(registry=registry, approval_bridge=bridge, project_root=tmp_path)
    plan = TaskPlan(
        plan_id="multi-plan",
        intent="multi_step",
        steps=[
            TaskStep("step-1", "first", "risk.first"),
            TaskStep("step-2", "middle", "safe.middle"),
            TaskStep("step-3", "last", "risk.last"),
        ],
    )

    first_wait = agent.executor.execute(plan)
    agent.approval_service.approve(first_wait.approval_ids[0], "reviewer")
    second_wait = agent.resume_approval(first_wait.approval_ids[0])

    assert second_wait.status == "waiting_for_approval"
    assert calls == ["first", "middle"]
    assert second_wait.plan.steps[0].state == TaskStepState.COMPLETED
    assert second_wait.plan.steps[1].state == TaskStepState.COMPLETED
    assert second_wait.plan.steps[2].state == TaskStepState.WAITING_FOR_APPROVAL

    agent.approval_service.approve(second_wait.approval_ids[0], "reviewer")
    completed = agent.resume_approval(second_wait.approval_ids[0])
    assert completed.status == "completed"
    assert calls == ["first", "middle", "last"]
    assert all(step.state == TaskStepState.COMPLETED for step in completed.plan.steps)


def test_non_sensitive_plan_can_resume_after_core_restart(tmp_path):
    calls = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            "files.write",
            "Write a file",
            requires_approval=True,
            risk_level=ToolRiskLevel.HIGH,
            handler=lambda payload: calls.append(dict(payload)) or "written",
        )
    )
    first = AgentCore(
        registry=registry,
        approval_bridge=AgentApprovalBridge(queue=NativeApprovalQueue(tmp_path)),
        project_root=tmp_path,
    )
    plan = TaskPlan(
        "restart-plan",
        "write_file",
        [TaskStep("write-step", "write", "files.write", {"path": "note.md", "content": "hello"})],
    )
    waiting = first.executor.execute(plan)
    first.approval_service.approve(waiting.approval_ids[0], "reviewer")

    restarted = AgentCore(
        registry=registry,
        approval_bridge=AgentApprovalBridge(queue=NativeApprovalQueue(tmp_path)),
        project_root=tmp_path,
    )
    completed = restarted.resume_approval(waiting.approval_ids[0])

    assert completed.status == "completed"
    assert calls == [{"path": "note.md", "content": "hello"}]


def test_plan_store_mark_completed(tmp_path):
    store = AgentPlanStore(tmp_path)
    plan = TaskPlan("plan-1", "test", [TaskStep("step-1", "done", state=TaskStepState.COMPLETED)])
    store.save(plan)

    completed = store.mark_completed(plan.plan_id)

    assert completed.metadata["status"] == "completed"
    assert store.load(plan.plan_id).metadata["status"] == "completed"
