from secondbrain.desktop.gui.gui_shell import GuiShell
from secondbrain.desktop.gui.gui_state import GuiState
from secondbrain.desktop.gui.module_registry import ModuleRegistry

def test_shell_model_contains_sidebar_entries():
    shell = GuiShell(ModuleRegistry.defaults(), GuiState(active_module="dashboard", startup_status="ready"))
    model = shell.model()
    assert model.status == "ready"
    assert any(item["id"] == "search" for item in model.sidebar)
