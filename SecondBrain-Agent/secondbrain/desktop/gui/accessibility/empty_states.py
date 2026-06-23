from __future__ import annotations
from .state_models import AccessibilityHint, UiSeverity, UiState, UiStateKind

class EmptyStateFactory:
    def documents(self) -> UiState:
        return UiState(UiStateKind.EMPTY, UiSeverity.INFO, "Keine Dokumente", "In diesem Workspace wurden noch keine Dokumente importiert.", "Datei importieren", hint=AccessibilityHint("Keine Dokumente", "status", "Dokumentenliste ist leer"))

    def search_results(self, query: str) -> UiState:
        safe_query = query.strip()[:120]
        return UiState(UiStateKind.EMPTY, UiSeverity.INFO, "Keine Treffer", f"Für '{safe_query}' wurden keine Treffer gefunden.", "Suchbegriff ändern oder Filter zurücksetzen", hint=AccessibilityHint("Keine Suchtreffer", "status", "Die Ergebnisliste ist leer"), metadata={"query": safe_query})

    def connectors(self) -> UiState:
        return UiState(UiStateKind.EMPTY, UiSeverity.INFO, "Keine Connectoren", "Es sind keine Connectoren konfiguriert.", "Connector hinzufügen", hint=AccessibilityHint("Keine Connectoren", "status", "Connector-Liste ist leer"))
