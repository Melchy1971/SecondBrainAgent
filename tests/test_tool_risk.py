from __future__ import annotations

import pytest

from secondbrain.agent import ToolDefinition, ToolRegistry, ToolRiskLevel


def test_high_risk_tool_requires_approval():
    registry = ToolRegistry()
    registry.register(ToolDefinition(
        "demo.write", "Write", risk_level=ToolRiskLevel.HIGH,
        requires_approval=True, handler=lambda payload: {"ok": True}, output_schema={"type": "object"},
    ))

    blocked = registry.run("demo.write", {})
    boolean_bypass = registry.run("demo.write", {}, approved=True)
    registry.set_approval_lookup(lambda approval_id: {
        "approval_id": approval_id,
        "status": "approved",
        "tool_name": "demo.write",
        "payload": {},
    })
    approved = registry.run("demo.write", {}, approval={"approval_id": "approval-1"})

    assert blocked.success is False
    assert "tool_requires_approval" in blocked.error
    assert boolean_bypass.success is False
    assert approved.success is True


def test_legacy_scope_and_approval_contract_remains_enforced(tmp_path):
    registry = ToolRegistry(tmp_path)
    registry.register(ToolDefinition(
        "demo.secure", "Secure", input_schema={}, output_schema={"type": "object"},
        scopes=("demo.execute",), risk_level=ToolRiskLevel.CRITICAL,
        requires_approval=True, handler=lambda payload: {"ok": True},
    ))

    with pytest.raises(PermissionError, match="approval"):
        registry.execute("demo.secure", {}, ["demo.execute"], approved=False)
    registry.set_approval_lookup(lambda approval_id: {
        "approval_id": approval_id,
        "status": "approved",
        "tool_name": "demo.secure",
        "payload": {},
    })
    with pytest.raises(PermissionError, match="scope"):
        registry.execute(
            "demo.secure",
            {},
            [],
            approval={"approval_id": "approval-2"},
        )
    result = registry.execute(
        "demo.secure",
        {},
        ["demo.execute"],
        approval={"approval_id": "approval-2"},
    )
    assert result["status"] == "success"
