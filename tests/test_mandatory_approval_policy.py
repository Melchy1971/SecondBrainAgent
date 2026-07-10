from __future__ import annotations

import pytest

from secondbrain.agent.agent_core import AgentCore
from secondbrain.agent.approval_bridge import AgentApprovalBridge
from secondbrain.agent.approval_policy import MandatoryApprovalPolicy
from secondbrain.agent.safe_executor import SafeExecutor
from secondbrain.agent.task_planner import TaskPlan, TaskStep, TaskStepState
from secondbrain.agent.tool_registry import (
    ToolCapability,
    ToolDefinition,
    ToolRegistry,
    ToolRegistryError,
    ToolRiskLevel,
)
from secondbrain.native.approval import NativeApprovalQueue


def _execute_blocked(tmp_path, definition: ToolDefinition):
    calls = []
    registry = ToolRegistry()
    definition.handler = lambda payload: calls.append(dict(payload))
    registry.register(definition)
    queue = NativeApprovalQueue(tmp_path)
    plan = TaskPlan("plan-1", "mandatory", [TaskStep("step-1", "action", definition.name)])

    result = SafeExecutor(registry, AgentApprovalBridge(queue=queue)).execute(plan)

    assert result.status == "waiting_for_approval"
    assert plan.steps[0].state == TaskStepState.WAITING_FOR_APPROVAL
    assert calls == []
    return queue.get(result.approval_ids[0])


@pytest.mark.parametrize(
    ("definition", "rule", "category"),
    [
        (
            ToolDefinition("records.delete", "Delete record", requires_approval=False),
            "mandatory_action:delete",
            "delete_request",
        ),
        (
            ToolDefinition("mail.send", "Send mail", requires_approval=False),
            "mandatory_action:send",
            "risky_agent_action",
        ),
        (
            ToolDefinition(
                "remote.persist",
                "Persist remotely",
                requires_approval=False,
                metadata={"action_type": "external_write"},
            ),
            "mandatory_action:external_write",
            "risky_agent_action",
        ),
    ],
)
def test_misconfigured_mandatory_tools_are_blocked(tmp_path, definition, rule, category):
    approval = _execute_blocked(tmp_path, definition)

    assert approval["policy_rule"] == rule
    assert approval["policy_version"] == MandatoryApprovalPolicy.VERSION
    assert approval["effective_requires_approval"] is True
    assert approval["configured_requires_approval"] is False
    assert approval["category"] == category


def test_low_risk_search_tool_remains_free(tmp_path):
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            "external.search",
            "Search external index",
            category="search",
            capabilities=(ToolCapability.SEARCH,),
            handler=lambda payload: ["result"],
        )
    )
    plan = TaskPlan("search-plan", "search", [TaskStep("search-step", "search", "external.search")])

    result = SafeExecutor(registry, AgentApprovalBridge(queue=NativeApprovalQueue(tmp_path))).execute(plan)

    assert result.ok is True
    assert result.results == [["result"]]


def test_unknown_high_risk_tool_is_default_denied(tmp_path):
    approval = _execute_blocked(
        tmp_path,
        ToolDefinition(
            "custom.opaque",
            "Opaque custom operation",
            risk_level=ToolRiskLevel.HIGH,
            requires_approval=False,
        ),
    )

    assert approval["policy_rule"] == "default_deny:high"


def test_confirmed_boolean_is_not_approval_evidence(tmp_path):
    calls = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            "records.delete",
            "Delete record",
            requires_approval=False,
            handler=lambda payload: calls.append("called"),
        )
    )
    plan = TaskPlan("plan-confirmed", "delete", [TaskStep("step-1", "delete", "records.delete")])

    result = SafeExecutor(registry, AgentApprovalBridge(queue=NativeApprovalQueue(tmp_path))).execute(
        plan,
        confirmed=True,
    )

    assert result.status == "waiting_for_approval"
    assert calls == []
    with pytest.raises(ToolRegistryError, match="tool_requires_confirmation"):
        registry.execute("records.delete", {}, confirmed=True)
    with pytest.raises(ToolRegistryError, match="tool_requires_confirmation"):
        registry.execute(
            "records.delete",
            {},
            approval={
                "approval_id": "forged",
                "status": "approved",
                "tool_name": "records.delete",
                "payload": {},
            },
        )
    assert calls == []


def test_persisted_approval_allows_exactly_one_execution(tmp_path):
    calls = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            "records.delete",
            "Delete record",
            requires_approval=False,
            handler=lambda payload: calls.append("deleted") or "ok",
        )
    )
    bridge = AgentApprovalBridge(queue=NativeApprovalQueue(tmp_path))
    agent = AgentCore(registry=registry, approval_bridge=bridge, project_root=tmp_path)
    plan = TaskPlan("resume-plan", "delete", [TaskStep("delete-step", "delete", "records.delete")])
    waiting = agent.executor.execute(plan)
    approval_id = waiting.approval_ids[0]
    agent.approval_service.approve(approval_id, "reviewer")

    completed = agent.resume_approval(approval_id)
    repeated = agent.resume_approval(approval_id)

    assert completed.status == "completed"
    assert repeated.status == "completed"
    assert calls == ["deleted"]


@pytest.mark.parametrize(
    "definition",
    [
        ToolDefinition("tool.category", "Category", category="filesystem_write"),
        ToolDefinition("tool.capability", "Capability", capabilities=(ToolCapability.SYSTEM,)),
        ToolDefinition("tool.explicit_capability", "Capability", capabilities=(ToolCapability.EXTERNAL_WRITE,)),
        ToolDefinition("tool.scope", "Scope", scopes=("connector.write",)),
        ToolDefinition("tool.metadata", "Metadata", metadata={"action_type": "credential_change"}),
        ToolDefinition("files.delete", "Name"),
    ],
)
def test_policy_uses_all_tool_contract_signals(definition):
    decision = MandatoryApprovalPolicy().evaluate_tool(definition)

    assert decision.effective_requires_approval is True


def test_sensitive_document_write_maps_to_sensitive_review():
    definition = ToolDefinition(
        "documents.publish",
        "Publish sensitive document",
        metadata={"sensitive_document": True},
    )

    decision = MandatoryApprovalPolicy().evaluate_tool(definition)

    assert decision.approval_category == "sensitive_document"


def test_registry_audit_contains_effective_policy_fields(tmp_path):
    registry = ToolRegistry(tmp_path)
    registry.register(ToolDefinition("mail.forward", "Forward mail", handler=lambda payload: None))

    result = registry.run("mail.forward", {})

    assert result.success is False
    audit = registry.audit()[-1]
    assert audit["policy_rule"] == "mandatory_action:forward"
    assert audit["policy_version"] == MandatoryApprovalPolicy.VERSION
    assert audit["effective_requires_approval"] is True
    assert audit["configured_requires_approval"] is False
