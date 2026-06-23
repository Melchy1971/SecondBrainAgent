from secondbrain.desktop.gui.gui_state import GuiState
from secondbrain.desktop.gui.gui_router import GuiRouter
from secondbrain.desktop.gui.module_registry import ModuleRegistry

def test_router_navigates_and_updates_state():
    state = GuiState()
    router = GuiRouter(ModuleRegistry.defaults(), state)
    result = router.navigate("search")
    assert result.route == "/search"
    assert state.active_module == "search"
    assert "search" in state.open_tabs

def test_router_resolves_route():
    router = GuiRouter(ModuleRegistry.defaults(), GuiState())
    assert router.resolve_route("/documents").module_id == "documents"
