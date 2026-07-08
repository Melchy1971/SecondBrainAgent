import pytest
from secondbrain.desktop.jobs import JobRegistry


def test_registry_registers_and_lists_jobs():
    registry = JobRegistry()
    registry.register("diagnostics", lambda meta: {"ok": True}, description="Run diagnostics")
    assert registry.has("diagnostics")
    assert list(registry.names()) == ["diagnostics"]
    assert registry.get("diagnostics").description == "Run diagnostics"


def test_registry_rejects_unknown_job():
    registry = JobRegistry()
    with pytest.raises(KeyError):
        registry.get("missing")
