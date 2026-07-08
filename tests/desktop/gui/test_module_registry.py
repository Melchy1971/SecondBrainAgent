from secondbrain.desktop.gui.module_registry import ModuleRegistry, GuiModule
import pytest

def test_default_registry_contains_core_modules():
    registry = ModuleRegistry.defaults()
    assert registry.has("dashboard")
    assert registry.has("documents")
    assert registry.has("settings")
    assert len(registry.list_modules()) == 8

def test_register_rejects_invalid_route():
    registry = ModuleRegistry()
    with pytest.raises(ValueError):
        registry.register(GuiModule("x", "X", "missing-slash"))
