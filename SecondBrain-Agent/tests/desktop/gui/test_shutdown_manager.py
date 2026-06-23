from secondbrain.desktop.gui.gui_state import GuiState
from secondbrain.desktop.gui.shutdown_manager import ShutdownManager

def test_shutdown_returns_saved_state():
    state = GuiState(active_module="settings")
    result = ShutdownManager(state).shutdown()
    assert result.status == "STOPPED"
    assert result.saved_state["startup_status"] == "stopped"
