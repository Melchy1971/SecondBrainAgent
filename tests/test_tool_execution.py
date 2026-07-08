from __future__ import annotations

import pytest

from secondbrain.agent import ToolDefinition, ToolInputSchema, ToolRegistry


def test_execution_validates_input_and_returns_structured_result():
    registry = ToolRegistry()
    registry.register(ToolDefinition(
        "demo.echo", "Echo", input_schema=ToolInputSchema({"text": {"type": "string"}}, ("text",), False),
        output_schema={"type": "object"}, handler=lambda payload: {"echo": payload["text"]},
    ))

    result = registry.run("demo.echo", {"text": "ok"})
    invalid = registry.run("demo.echo", {"text": 3})

    assert result.success is True
    assert result.output == {"echo": "ok"}
    assert invalid.success is False
    assert "invalid_tool_input_type:text:string" in invalid.error


def test_disabled_tool_cannot_execute():
    registry = ToolRegistry()
    registry.register(ToolDefinition("demo.echo", "Echo", handler=lambda payload: payload))
    registry.set_enabled("demo.echo", False)

    with pytest.raises(PermissionError, match="tool_disabled"):
        registry.execute("demo.echo", {})


def test_filesystem_tool_is_confined_to_project_root(tmp_path):
    from secondbrain.agent import ToolDiscovery

    registry = ToolRegistry()
    ToolDiscovery(tmp_path, registry).discover()
    inside = tmp_path / "note.txt"
    inside.write_text("content", encoding="utf-8")

    assert registry.run("filesystem.read", {"path": "note.txt"}).output["content"] == "content"
    outside = registry.run("filesystem.read", {"path": str(tmp_path.parent / "outside.txt")})
    assert outside.success is False
    assert "filesystem_path_outside_project" in outside.error
