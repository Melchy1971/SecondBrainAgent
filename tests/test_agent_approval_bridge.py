from __future__ import annotations

import pytest

from secondbrain.agent.agent_core import AgentCore, AgentRequest
from secondbrain.agent.approval_bridge import AgentApprovalBridge
from secondbrain.agent.intent_router import IntentRoute, IntentRouter
from secondbrain.agent.safe_executor import SafeExecutor
from secondbrain.agent.task_planner import TaskPlanner, TaskStepState
from secondbrain.agent.tool_registry import (
    ToolDefinition,
    ToolInputSchema,
    ToolRegistry,
    ToolRiskLevel,
)
from secondbrain.native.approval import NativeApprovalQueue


def test_agent_core_queues_approval_without_executing_sensitive_payload(tmp_path):
    calls: list[dict[str, str]] = []
    queue = NativeApprovalQueue(tmp_path)
    bridge = AgentApprovalBridge(queue=queue)
    router = IntentRouter()
    router.add_keyword_rule(
        "delete",
        IntentRoute(
            intent="delete_document",
            tool_name="documents.delete",
            parameters={"document_id": "doc-1", "token": "secret-value"},
        ),
    )
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            "documents.delete",
            "Delete a document",
            category="documents",
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
            handler=lambda payload: calls.append(dict(payload)),
        )
    )
    agent = AgentCore(router=router, registry=registry, approval_bridge=bridge)

    response = agent.handle(AgentRequest(text="delete it", workspace_id="workspace-1"))

    assert response.ok is False
    assert response.status == "waiting_for_approval"
    assert response.message == "waiting_for_approval"
    assert response.errors == []
    assert len(response.approval_ids) == 1
    assert response.plan.steps[0].state == TaskStepState.WAITING_FOR_APPROVAL
    assert calls == []

    approvals = queue.list(status="pending")
    assert len(approvals) == 1
    approval = approvals[0]
    assert approval["approval_id"] == response.approval_ids[0]
    assert approval["plan_id"] == response.plan.plan_id
    assert approval["step_id"] == response.plan.steps[0].step_id
    assert approval["tool_name"] == "documents.delete"
    assert approval["intent"] == "delete_document"
    assert approval["category"] == "delete_request"
    assert approval["risk_level"] == "high"
    assert approval["payload"] == {"document_id": "doc-1", "token": "***"}
    assert approval["workspace_id"] == "workspace-1"
    assert approval["created_at"]


def test_execution_result_identifies_waiting_step(tmp_path):
    queue = NativeApprovalQueue(tmp_path)
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            "connector.permissions.update",
            "Update connector permissions",
            risk_level=ToolRiskLevel.CRITICAL,
            requires_approval=True,
            handler=lambda payload: payload,
        )
    )
    plan = TaskPlanner().create_single_tool_plan(
        intent="change_permissions",
        tool_name="connector.permissions.update",
    )

    result = SafeExecutor(registry, AgentApprovalBridge(queue=queue)).execute(plan)

    assert result.status == "waiting_for_approval"
    assert result.approval_ids
    assert result.waiting_step_ids == [plan.steps[0].step_id]
    assert queue.list()[0]["category"] == "connector_permission_change"


def test_low_risk_tool_executes_without_approval(tmp_path):
    queue = NativeApprovalQueue(tmp_path)
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            "documents.read",
            "Read a document",
            risk_level=ToolRiskLevel.LOW,
            handler=lambda payload: {"value": payload["value"]},
        )
    )
    plan = TaskPlanner().create_single_tool_plan(
        intent="read_document",
        tool_name="documents.read",
        payload={"value": "ok"},
    )

    result = SafeExecutor(registry, AgentApprovalBridge(queue=queue)).execute(plan)

    assert result.ok is True
    assert result.status == "completed"
    assert result.results == [{"value": "ok"}]
    assert plan.steps[0].state == TaskStepState.COMPLETED
    assert queue.list() == []


@pytest.mark.parametrize(
    ("tool_name", "expected"),
    [
        ("records.remove", "delete_request"),
        ("connector.oauth.update", "connector_permission_change"),
        ("external.send", "risky_agent_action"),
    ],
)
def test_category_mapping(tool_name, expected):
    assert AgentApprovalBridge.category_for(tool_name) == expected
