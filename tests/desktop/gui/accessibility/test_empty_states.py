from secondbrain.desktop.gui.accessibility.empty_states import EmptyStateFactory
from secondbrain.desktop.gui.accessibility.state_models import UiStateKind


def test_search_empty_state_sanitizes_long_query():
    state = EmptyStateFactory().search_results("x" * 200)
    assert state.kind == UiStateKind.EMPTY
    assert len(state.metadata["query"]) == 120
    assert state.recovery_action == "Suchbegriff ändern oder Filter zurücksetzen"


def test_document_empty_state_has_actionable_recovery():
    state = EmptyStateFactory().documents()
    assert state.recovery_action == "Datei importieren"
    assert state.hint.label == "Keine Dokumente"
