from secondbrain.desktop.gui.gui_state import GuiState

def test_state_snapshot_contains_gui_fields():
    state = GuiState()
    state.activate("documents")
    snapshot = state.snapshot()
    assert snapshot["active_module"] == "documents"
    assert snapshot["selected_workspace"] == "default"
    assert snapshot["recovery_mode"] is False
