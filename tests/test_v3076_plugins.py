from __future__ import annotations

import json
from pathlib import Path

import pytest

from secondbrain.agent.tool_registry import ToolRegistry, ToolRegistryError
from secondbrain.plugins import (
    PluginLoader,
    PluginManifest,
    PluginManifestError,
    PluginMarketplace,
    PluginPermissionPolicy,
    PluginSandbox,
    PluginSettings,
)


def _manifest(**overrides):
    payload = {
        "id": "acme.notes",
        "name": "ACME Notes",
        "version": "1.2.3",
        "api_version": "1",
        "description": "Adds a namespaced notes tool.",
        "entrypoint": "plugin.py:register",
        "permissions": ["tools.register", "settings.read", "settings.write", "workspace.read"],
        "capabilities": ["notes"],
        "settings": {
            "prefix": {"type": "string", "default": "Note"},
            "limit": {"type": "integer", "default": 10},
            "credential": {"type": "string", "secret": True, "default": "secret://unset"},
        },
        "marketplace": {
            "publisher": "ACME", "license": "MIT", "homepage": "https://example.invalid",
            "tags": ["notes"],
        },
    }
    payload.update(overrides)
    return payload


def _write_plugin(root: Path, *, payload=None, source=None) -> Path:
    plugin = root / "plugins" / "acme-notes"
    plugin.mkdir(parents=True)
    (plugin / "plugin.json").write_text(json.dumps(payload or _manifest()), encoding="utf-8")
    (plugin / "plugin.py").write_text(source or """
def register(api):
    prefix = api.get_setting("prefix")
    api.register_tool(
        "plugin.acme.notes.echo",
        "Echo a note",
        lambda payload: {"text": f"{prefix}: {payload['text']}"},
        input_schema={"properties": {"text": {"type": "string"}}, "required": ["text"], "additionalProperties": False},
    )
""", encoding="utf-8")
    return plugin


def test_plugin_manifest_validates_schema_permissions_and_entrypoint() -> None:
    manifest = PluginManifest.from_dict(_manifest())
    assert manifest.id == "acme.notes"
    assert manifest.api_version == "1"
    assert manifest.settings_schema["limit"]["type"] == "integer"

    with pytest.raises(PluginManifestError, match="invalid_plugin_id"):
        PluginManifest.from_dict(_manifest(id="../escape"))
    with pytest.raises(PluginManifestError, match="unsupported_plugin_api"):
        PluginManifest.from_dict(_manifest(api_version="2"))
    with pytest.raises(PluginManifestError, match="path_traversal"):
        PluginManifest.from_dict(_manifest(entrypoint="../plugin.py:register"))
    with pytest.raises(PluginManifestError, match="unknown_plugin_permission"):
        PluginManifest.from_dict(_manifest(permissions=["root.everything"]))
    with pytest.raises(PluginManifestError, match="field_must_be_array"):
        PluginManifest.from_dict(_manifest(permissions="tools.register"))
    with pytest.raises(PluginManifestError, match="enabled_must_be_boolean"):
        PluginManifest.from_dict(_manifest(enabled="false"))


def test_discovery_is_declarative_and_does_not_execute_plugin(tmp_path: Path) -> None:
    marker = tmp_path / "executed.txt"
    source = f"from pathlib import Path\nPath({str(marker)!r}).write_text('yes')\ndef register(api): pass\n"
    _write_plugin(tmp_path, source=source)
    loader = PluginLoader(tmp_path)

    plugins = loader.discover()

    assert [plugin.manifest.id for plugin in plugins] == ["acme.notes"]
    assert plugins[0].status == "discovered"
    assert not marker.exists()
    assert not (tmp_path / "runtime").exists()


def test_activation_requires_host_trust(tmp_path: Path) -> None:
    _write_plugin(tmp_path)
    loader = PluginLoader(tmp_path)
    loader.discover()
    with pytest.raises(PermissionError, match="plugin_not_trusted"):
        loader.activate("acme.notes")


def test_trusted_plugin_registers_only_in_existing_tool_registry(tmp_path: Path) -> None:
    _write_plugin(tmp_path)
    registry = ToolRegistry()
    loader = PluginLoader(
        tmp_path,
        tool_registry=registry,
        trusted_plugins={"acme.notes"},
        grants={"acme.notes": {"tools.register", "settings.read"}},
    )
    loader.discover()

    plugin = loader.activate("acme.notes")
    result = registry.run("plugin.acme.notes.echo", {"text": "hello"})

    assert plugin.status == "active"
    assert plugin.registered_tools == ("plugin.acme.notes.echo",)
    assert result.output == {"text": "Note: hello"}
    assert registry.get("plugin.acme.notes.echo").metadata["plugin_id"] == "acme.notes"
    assert loader.activate("acme.notes") is plugin

    loader.deactivate("acme.notes")
    assert plugin.status == "inactive"
    with pytest.raises(ToolRegistryError, match="tool_not_found"):
        registry.get("plugin.acme.notes.echo")


def test_plugin_api_enforces_declared_and_granted_permissions(tmp_path: Path) -> None:
    _write_plugin(tmp_path)
    loader = PluginLoader(
        tmp_path,
        tool_registry=ToolRegistry(),
        trusted_plugins={"acme.notes"},
        grants={"acme.notes": {"settings.read"}},
    )
    loader.discover()
    with pytest.raises(PermissionError, match="plugin_permission_not_granted"):
        loader.activate("acme.notes")
    assert loader.get("acme.notes").status == "error"


def test_failed_activation_rolls_back_registered_tools(tmp_path: Path) -> None:
    source = """
def register(api):
    api.register_tool("plugin.acme.notes.first", "first", lambda payload: {})
    raise RuntimeError("registration failed")
"""
    _write_plugin(tmp_path, source=source)
    registry = ToolRegistry()
    loader = PluginLoader(tmp_path, tool_registry=registry, trusted_plugins={"acme.notes"},
                          grants={"acme.notes": {"tools.register"}})
    loader.discover()
    with pytest.raises(RuntimeError, match="registration failed"):
        loader.activate("acme.notes")
    assert registry.has("plugin.acme.notes.first") is False


def test_plugin_tool_namespace_and_high_risk_approval_are_enforced(tmp_path: Path) -> None:
    source = """
def register(api):
    api.register_tool("wrong.name", "bad", lambda payload: {})
"""
    _write_plugin(tmp_path, source=source)
    loader = PluginLoader(tmp_path, tool_registry=ToolRegistry(), trusted_plugins={"acme.notes"},
                          grants={"acme.notes": {"tools.register"}})
    loader.discover()
    with pytest.raises(ValueError, match="plugin_tool_prefix_required"):
        loader.activate("acme.notes")

    source = """
def register(api):
    api.register_tool("plugin.acme.notes.write", "write", lambda payload: {}, risk_level="high")
"""
    (tmp_path / "plugins" / "acme-notes" / "plugin.py").write_text(source, encoding="utf-8")
    loader.get("acme.notes").status = "discovered"
    plugin = loader.activate("acme.notes")
    assert plugin.status == "active"
    blocked = loader.tool_registry.run("plugin.acme.notes.write")
    assert blocked.success is False
    assert "requires_approval" in (blocked.error or "")
    assert loader.tool_registry.run("plugin.acme.notes.write", approved=True).success is True


def test_plugin_sandbox_blocks_traversal_and_unauthorized_writes(tmp_path: Path) -> None:
    plugin_root = _write_plugin(tmp_path)
    (tmp_path / "readme.txt").write_text("safe", encoding="utf-8")
    policy = PluginPermissionPolicy(
        "acme.notes", declared={"workspace.read"}, granted={"workspace.read"},
    )
    sandbox = PluginSandbox(tmp_path, plugin_root, "acme.notes", policy)

    assert sandbox.read_text("readme.txt") == "safe"
    with pytest.raises(PermissionError, match="outside_root"):
        sandbox.read_text("../outside.txt")
    with pytest.raises(PermissionError, match="not_declared"):
        sandbox.write_text("new.txt", "blocked")
    with pytest.raises(PermissionError, match="plugin_data_path_outside_root"):
        sandbox.data_path("../other-plugin")
    (tmp_path / ".env").write_text("TOKEN=secret", encoding="utf-8")
    with pytest.raises(PermissionError, match="not_declared"):
        sandbox.read_text(".env")
    with pytest.raises(PermissionError, match="path_protected"):
        sandbox.workspace_path(".git/config")
    writable_policy = PluginPermissionPolicy(
        "acme.notes", declared={"workspace.write"}, granted={"workspace.write"},
    )
    writable = PluginSandbox(tmp_path, plugin_root, "acme.notes", writable_policy)
    with pytest.raises(PermissionError, match="settings_api_required"):
        writable.workspace_path("runtime/plugins/settings/acme.notes.json", write=True)


def test_plugin_settings_defaults_validation_and_secret_references(tmp_path: Path) -> None:
    manifest = PluginManifest.from_dict(_manifest())
    settings = PluginSettings(tmp_path, manifest)
    assert settings.load() == {"prefix": "Note", "limit": 10, "credential": "secret://unset"}
    assert not settings.path.exists()

    updated = settings.set("limit", 25)
    assert updated["limit"] == 25
    with pytest.raises(ValueError, match="invalid_plugin_setting_type"):
        settings.set("limit", True)
    with pytest.raises(ValueError, match="secret_reference_required"):
        settings.set("credential", "plaintext-secret")
    assert settings.set("credential", "secret://vault/acme")["credential"] == "secret://vault/acme"


def test_marketplace_preparation_is_offline_and_requires_package_checksum(tmp_path: Path) -> None:
    ready = PluginManifest.from_dict(_manifest())
    package_without_hash = PluginManifest.from_dict(_manifest(
        id="acme.package", marketplace={
            "publisher": "ACME", "license": "MIT", "homepage": "https://example.invalid",
            "package_url": "https://example.invalid/plugin.zip",
        },
    ))
    marketplace = PluginMarketplace()
    catalog = marketplace.prepare([package_without_hash, ready])

    assert catalog["mode"] == "metadata_only"
    assert catalog["install_supported"] is False
    assert catalog["count"] == 2
    assert catalog["ready"] == 1
    package = next(row for row in catalog["plugins"] if row["plugin_id"] == "acme.package")
    assert "package_checksum_required" in package["issues"]
    target = marketplace.export(catalog, tmp_path / "catalog.json")
    assert json.loads(target.read_text(encoding="utf-8"))["schema"] == marketplace.SCHEMA


def test_discovery_reports_invalid_and_duplicate_manifests(tmp_path: Path) -> None:
    _write_plugin(tmp_path)
    duplicate = tmp_path / "plugins" / "duplicate"
    duplicate.mkdir()
    (duplicate / "plugin.json").write_text(json.dumps(_manifest()), encoding="utf-8")
    invalid = tmp_path / "plugins" / "invalid"
    invalid.mkdir()
    (invalid / "plugin.json").write_text("not json", encoding="utf-8")

    loader = PluginLoader(tmp_path)
    plugins = loader.discover()

    assert len(plugins) == 1
    assert len(loader.errors) == 2
    assert any("duplicate_plugin_id" in row["error"] for row in loader.errors)
    assert any("unreadable" in row["error"] for row in loader.errors)
