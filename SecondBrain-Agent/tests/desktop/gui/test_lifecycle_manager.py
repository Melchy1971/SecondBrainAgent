from secondbrain.desktop.gui.gui_state import GuiState
from secondbrain.desktop.gui.lifecycle_manager import LifecycleManager
from secondbrain.desktop.gui.startup_checks import StartupChecks, StartupCheck

def test_lifecycle_reaches_ready_when_checks_pass():
    state = GuiState()
    result = LifecycleManager(state).start()
    assert result.status == "READY"
    assert state.startup_status == "ready"

def test_lifecycle_enters_recovery_when_required_check_fails():
    state = GuiState()
    checks = StartupChecks([StartupCheck("settings", True, lambda: False)])
    result = LifecycleManager(state, checks).start()
    assert result.status == "BLOCKED"
    assert result.recovery_mode is True
