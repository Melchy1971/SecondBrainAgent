from __future__ import annotations

from secondbrain.agent import ToolDiscovery, ToolRegistry


def test_discovery_registers_all_required_existing_categories(tmp_path):
    registry = ToolRegistry(tmp_path / "runtime")
    tools = ToolDiscovery(tmp_path, registry).discover()

    categories = {tool.category for tool in tools}
    assert {
        "search", "documents", "import", "memory", "agents", "jobs",
        "notifications", "settings", "voice", "updates", "github", "filesystem",
    } <= categories
    assert all(tool.handler is not None for tool in tools)


def test_discovery_is_idempotent_and_health_uses_same_registry(tmp_path):
    registry = ToolRegistry(tmp_path / "runtime")
    discovery = ToolDiscovery(tmp_path, registry)
    first = discovery.discover()
    second = discovery.discover()

    assert len(first) == len(second)
    health = registry.health()
    assert health["healthy"] is True
    assert health["handlers"] == len(second)
