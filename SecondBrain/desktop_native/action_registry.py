from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, Callable, Mapping


class ActionRisk(StrEnum):
    READ = "read"
    WRITE = "write"
    EXTERNAL_WRITE = "external_write"


ActionHandler = Callable[[Mapping[str, Any]], Any]
Availability = Callable[[], bool]


@dataclass(frozen=True, slots=True)
class ActionDefinition:
    id: str
    title: str
    description: str = ""
    aliases: tuple[str, ...] = ()
    parameters: Mapping[str, Any] = field(default_factory=dict)
    risk: ActionRisk = ActionRisk.READ
    requires_confirmation: bool = False
    requires_approval: bool = False
    requires_workspace: bool = False
    handler: ActionHandler | None = field(default=None, repr=False, compare=False)
    availability: Availability | None = field(default=None, repr=False, compare=False)
    capability_source: str = "application_core"

    def is_available(self) -> bool:
        return self.handler is not None and (self.availability is None or self.availability())

    def public_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("handler", None)
        payload.pop("availability", None)
        payload["available"] = self.is_available()
        return payload


class ActionRegistry:
    """Single action catalogue shared by desktop, voice, web and CLI adapters."""

    def __init__(self) -> None:
        self._actions: dict[str, ActionDefinition] = {}
        self._aliases: dict[str, str] = {}

    def register(self, action: ActionDefinition) -> None:
        if action.id in self._actions:
            raise ValueError(f"duplicate action id: {action.id}")
        normalized = {_normalize(alias) for alias in action.aliases}
        collisions = normalized.intersection(self._aliases)
        if collisions:
            raise ValueError(f"duplicate action alias: {sorted(collisions)[0]}")
        self._actions[action.id] = action
        self._aliases.update({alias: action.id for alias in normalized})

    def get(self, action_id: str) -> ActionDefinition:
        try:
            return self._actions[action_id]
        except KeyError as exc:
            raise KeyError(f"unknown action: {action_id}") from exc

    def resolve_alias(self, utterance: str) -> ActionDefinition | None:
        action_id = self._aliases.get(_normalize(utterance))
        return self._actions.get(action_id) if action_id else None

    def list(self) -> tuple[ActionDefinition, ...]:
        return tuple(self._actions.values())


def _normalize(value: str) -> str:
    return " ".join(value.casefold().strip().split())


def build_core_registry(handler: ActionHandler) -> ActionRegistry:
    registry = ActionRegistry()
    views = {
        "dashboard": "Dashboard", "tasks": "Aufgaben", "projects": "Projekte",
        "documents": "Dokumente", "search": "Suche", "memory": "Memory",
        "calendar": "Kalender", "mail": "Mail", "jobs": "Jobs",
        "approvals": "Freigaben", "settings": "Einstellungen", "diagnostics": "Diagnose",
    }
    for view, title in views.items():
        registry.register(ActionDefinition(
            id=f"navigation.{view}", title=f"{title} öffnen",
            aliases=(f"öffne {title.lower()}", f"zeige {title.lower()}"),
            parameters={"view": {"type": "string", "const": view}}, handler=handler,
            capability_source="native_navigation",
        ))
    registry.register(ActionDefinition(
        id="assistant.ask", title="Assistent fragen", aliases=(),
        parameters={"text": {"type": "string", "minLength": 1}}, handler=handler,
        capability_source="rag_chat_service",
    ))
    registry.register(ActionDefinition(
        id="documents.import", title="Datei importieren", aliases=("importiere datei",),
        risk=ActionRisk.WRITE, requires_confirmation=True, requires_workspace=True,
        parameters={"path": {"type": "string", "minLength": 1}}, handler=handler,
        capability_source="document_import_service",
    ))
    registry.register(ActionDefinition(
        id="calendar.create", title="Termin erstellen", aliases=("erstelle termin", "neuer termin"),
        risk=ActionRisk.EXTERNAL_WRITE, requires_approval=True, requires_workspace=True,
        parameters={"title": {"type": "string", "minLength": 1}, "when": {"type": "string", "minLength": 1}}, handler=handler,
        capability_source="calendar_assistant",
    ))
    registry.register(ActionDefinition(
        id="mail.send", title="E-Mail senden", aliases=("sende antwort", "sende mail"),
        risk=ActionRisk.EXTERNAL_WRITE, requires_approval=True, requires_workspace=True,
        parameters={"recipient": {"type": "string", "minLength": 1}, "body": {"type": "string", "minLength": 1}}, handler=handler,
        capability_source="mail_assistant",
    ))
    return registry
