from __future__ import annotations
from dataclasses import dataclass
from .state_models import AccessibilityHint, UiSeverity, UiState, UiStateKind

@dataclass(frozen=True)
class ErrorDefinition:
    code: str
    title: str
    message: str
    severity: UiSeverity
    recovery_action: str

class ErrorCatalog:
    def __init__(self) -> None:
        self._errors: dict[str, ErrorDefinition] = {}
        self.register(ErrorDefinition("settings_corrupt", "Settings beschädigt", "Die Einstellungen konnten nicht geladen werden.", UiSeverity.ERROR, "Recovery aus letztem Snapshot starten"))
        self.register(ErrorDefinition("workspace_missing", "Workspace fehlt", "Es ist kein gültiger Workspace ausgewählt.", UiSeverity.WARNING, "Default-Workspace erstellen oder auswählen"))
        self.register(ErrorDefinition("rag_unavailable", "RAG nicht verfügbar", "Die semantische Suche ist aktuell nicht bereit.", UiSeverity.WARNING, "Indexstatus prüfen und Reindex starten"))
        self.register(ErrorDefinition("connector_failed", "Connector fehlgeschlagen", "Ein Connector konnte nicht synchronisieren.", UiSeverity.ERROR, "Connector-Konfiguration prüfen und Sync wiederholen"))
        self.register(ErrorDefinition("unknown", "Unbekannter Fehler", "Ein unerwarteter Fehler ist aufgetreten.", UiSeverity.ERROR, "Diagnose öffnen"))

    def register(self, definition: ErrorDefinition) -> None:
        if not definition.code:
            raise ValueError("error code must not be empty")
        self._errors[definition.code] = definition

    def get(self, code: str) -> ErrorDefinition:
        return self._errors.get(code, self._errors["unknown"])

    def to_state(self, code: str, detail: str | None = None) -> UiState:
        definition = self.get(code)
        return UiState(
            kind=UiStateKind.ERROR,
            severity=definition.severity,
            title=definition.title,
            message=definition.message,
            recovery_action=definition.recovery_action,
            technical_detail=detail,
            hint=AccessibilityHint(label=definition.title, role="alert", description=definition.message, live_region="assertive"),
            metadata={"error_code": definition.code},
        )
