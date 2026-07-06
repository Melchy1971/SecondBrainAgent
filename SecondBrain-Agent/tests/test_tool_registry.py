from __future__ import annotations

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
