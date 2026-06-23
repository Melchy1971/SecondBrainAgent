from secondbrain.desktop.gui.accessibility.error_state_service import ErrorStateService
from secondbrain.desktop.gui.accessibility.state_models import UiStateKind


def test_known_error_contains_recovery_and_alert_hint():
    state = ErrorStateService().error("settings_corrupt", "json decode failed")
    assert state.kind == UiStateKind.ERROR
    assert state.is_blocking()
    assert state.recovery_action == "Recovery aus letztem Snapshot starten"
    assert state.hint.role == "alert"
    assert state.hint.live_region == "assertive"


def test_unknown_error_falls_back_to_generic_state():
    state = ErrorStateService().error("does_not_exist")
    assert state.metadata["error_code"] == "unknown"
    assert state.title == "Unbekannter Fehler"
