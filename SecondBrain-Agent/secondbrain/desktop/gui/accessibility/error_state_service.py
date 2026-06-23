from __future__ import annotations
from .empty_states import EmptyStateFactory
from .error_catalog import ErrorCatalog
from .state_models import AccessibilityHint, UiSeverity, UiState, UiStateKind

class ErrorStateService:
    def __init__(self, catalog: ErrorCatalog | None = None, empty_states: EmptyStateFactory | None = None) -> None:
        self.catalog = catalog or ErrorCatalog()
        self.empty_states = empty_states or EmptyStateFactory()

    def loading(self, title: str = "Lädt", message: str = "Daten werden geladen.") -> UiState:
        return UiState(UiStateKind.LOADING, UiSeverity.INFO, title, message, hint=AccessibilityHint(title, "status", message, live_region="polite"))

    def ready(self, title: str = "Bereit", message: str = "Ansicht ist bereit.") -> UiState:
        return UiState(UiStateKind.READY, UiSeverity.SUCCESS, title, message, hint=AccessibilityHint(title, "status", message))

    def error(self, code: str, detail: str | None = None) -> UiState:
        return self.catalog.to_state(code, detail)

    def warning(self, title: str, message: str, recovery_action: str | None = None) -> UiState:
        return UiState(UiStateKind.WARNING, UiSeverity.WARNING, title, message, recovery_action, hint=AccessibilityHint(title, "alert", message))
