from secondbrain.desktop.gui.accessibility.a11y_audit import AccessibilityAudit
from secondbrain.desktop.gui.accessibility.error_state_service import ErrorStateService
from secondbrain.desktop.gui.accessibility.state_models import UiSeverity, UiState, UiStateKind


def test_audit_passes_valid_blocking_error():
    state = ErrorStateService().error("connector_failed")
    assert AccessibilityAudit().passes(state)


def test_audit_flags_blocking_state_without_recovery():
    state = UiState(UiStateKind.ERROR, UiSeverity.ERROR, "Fehler", "Kaputt")
    issues = AccessibilityAudit().audit_state(state)
    assert any(issue.code == "missing_recovery" for issue in issues)
    assert not AccessibilityAudit().passes(state)
