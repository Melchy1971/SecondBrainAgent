from __future__ import annotations

import time

from secondbrain.agent import (
    ToolCapability,
    ToolDefinition,
    ToolInputSchema,
    ToolRegistry,
    ToolRiskLevel,
)


def test_unified_registry_exposes_complete_tool_contract(tmp_path):
    registry = ToolRegistry(tmp_path)
    definition = ToolDefinition(
        "demo.echo",
        "Echo a value",
        category="demo",
        input_schema=ToolInputSchema({"value": {"type": "string"}}, ("value",), False),
        output_schema={"type": "object"},
        risk_level=ToolRiskLevel.LOW,
        handler=lambda payload: {"value": payload["value"]},
        capabilities=(ToolCapability.SYSTEM,),
    )

    registered = registry.register(definition)

    assert registered.name == "demo.echo"
    assert registered.input_schema.required == ("value",)
    assert registered.capabilities == (ToolCapability.SYSTEM,)
    assert registry.get("demo.echo").handler is not None


def test_enable_state_survives_registry_reload_and_handler_discovery(tmp_path):
    registry = ToolRegistry(tmp_path)
    registry.register(ToolDefinition("demo.echo", "Echo", handler=lambda payload: payload))
    registry.set_enabled("demo.echo", False)

    reloaded = ToolRegistry(tmp_path)
    assert reloaded.get("demo.echo").enabled is False
    assert reloaded.get("demo.echo").handler is None

    reloaded.upsert(ToolDefinition("demo.echo", "Echo", handler=lambda payload: payload))
    assert reloaded.get("demo.echo").enabled is False
    assert reloaded.get("demo.echo").handler is not None


def test_documented_positional_contract_is_supported():
    handler = lambda payload: {"ok": True}
    definition = ToolDefinition(
        "demo.positional", "Positional", "demo", {}, {"type": "object"},
        ToolRiskLevel.MEDIUM, False, True, handler,
    )
    assert definition.category == "demo"
    assert definition.risk_level == ToolRiskLevel.MEDIUM
    assert definition.handler is handler


def test_high_risk_auto_requires_approval_even_when_not_explicit(tmp_path):
    registry = ToolRegistry(tmp_path)
    definition = ToolDefinition(
        "demo.danger",
        "Dangerous",
        risk_level=ToolRiskLevel.HIGH,
        requires_approval=False,
        handler=lambda payload: {"ok": True},
        output_schema={"type": "object"},
    )
    registry.register(definition)

    blocked = registry.run("demo.danger", {})
    assert blocked.success is False
    assert "tool_requires_approval" in (blocked.error or "")


def test_timeout_retry_and_audit_metadata(tmp_path):
    registry = ToolRegistry(tmp_path)
    attempts = {"count": 0}

    def flaky(payload):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("transient")
        return {"ok": True}

    registry.register(
        ToolDefinition(
            "demo.flaky",
            "Flaky",
            category="system",
            input_schema=ToolInputSchema({}, (), False),
            output_schema={"type": "object"},
            handler=flaky,
            retry_count=1,
            timeout_seconds=1.0,
        )
    )

    success = registry.run("demo.flaky", {})
    assert success.success is True
    assert success.metadata.get("attempts") == 2

    registry.register(
        ToolDefinition(
            "demo.slow",
            "Slow",
            category="system",
            input_schema=ToolInputSchema({}, (), False),
            output_schema={"type": "object"},
            handler=lambda payload: (time.sleep(0.05), {"ok": True})[1],
            timeout_seconds=0.01,
        )
    )
    timeout = registry.run("demo.slow", {})
    assert timeout.success is False
    assert "tool_timeout" in (timeout.error or "")

    audit_rows = registry.audit(limit=10)
    assert audit_rows
    assert any(row.get("event") == "tool_run" for row in audit_rows)
    assert any("metadata" in row for row in audit_rows)
