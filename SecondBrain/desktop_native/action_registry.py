from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, Callable, Mapping

from .navigation import NAVIGATION_VIEWS


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

    def bound(action_id: str) -> ActionHandler:
        return lambda payload: handler({"action_id": action_id, **payload})

    for view, display, spoken in NAVIGATION_VIEWS:
        registry.register(ActionDefinition(
            id=f"navigation.{view}", title=f"{display} öffnen",
            aliases=(f"öffne {spoken.lower()}", f"zeige {spoken.lower()}"),
            parameters={"view": {"type": "string", "const": view}}, handler=bound(f"navigation.{view}"),
            capability_source="native_navigation",
        ))
    registry.register(ActionDefinition(
        id="assistant.ask", title="Assistent fragen", aliases=(),
        parameters={"text": {"type": "string", "minLength": 1}}, handler=bound("assistant.ask"),
        capability_source="rag_chat_service",
    ))
    registry.register(ActionDefinition(
        id="documents.import", title="Datei importieren", aliases=("importiere datei",),
        risk=ActionRisk.WRITE, requires_confirmation=True, requires_workspace=True,
        parameters={"path": {"type": "string", "minLength": 1}}, handler=bound("documents.import"),
        capability_source="document_import_service",
    ))
    registry.register(ActionDefinition(
        id="tasks.list", title="Aufgaben auflisten",
        aliases=("liste aufgaben", "welche aufgaben habe ich"),
        requires_workspace=True, handler=bound("tasks.list"),
        capability_source="desktop_task_service",
    ))
    registry.register(ActionDefinition(
        id="tasks.create", title="Aufgabe erstellen",
        aliases=("erstelle aufgabe", "neue aufgabe", "aufgabe erstellen"),
        risk=ActionRisk.WRITE, requires_confirmation=True, requires_workspace=True,
        parameters={
            "title": {"type": "string", "minLength": 1},
            "priority": {"type": "string", "enum": ["low", "medium", "high"]},
        },
        handler=bound("tasks.create"), capability_source="desktop_task_service",
    ))
    registry.register(ActionDefinition(
        id="tasks.complete", title="Aufgabe abschließen",
        aliases=("aufgabe abschliessen", "aufgabe abschließen", "erledige aufgabe"),
        risk=ActionRisk.WRITE, requires_confirmation=True, requires_workspace=True,
        parameters={"task": {"type": "string", "minLength": 1}},
        handler=bound("tasks.complete"), capability_source="desktop_task_service",
    ))
    registry.register(ActionDefinition(
        id="tasks.rename", title="Aufgabe umbenennen",
        aliases=("aufgabe umbenennen", "benenne aufgabe um"),
        risk=ActionRisk.WRITE, requires_confirmation=True, requires_workspace=True,
        parameters={
            "task": {"type": "string", "minLength": 1},
            "new_title": {"type": "string", "minLength": 1, "maxLength": 200},
        },
        handler=bound("tasks.rename"), capability_source="desktop_task_service",
    ))
    registry.register(ActionDefinition(
        id="tasks.archive", title="Aufgabe archivieren",
        aliases=("aufgabe archivieren", "archiviere aufgabe"),
        risk=ActionRisk.WRITE, requires_confirmation=True, requires_workspace=True,
        parameters={"task": {"type": "string", "minLength": 1}},
        handler=bound("tasks.archive"), capability_source="desktop_task_service",
    ))
    registry.register(ActionDefinition(
        id="tasks.restore", title="Aufgabe wiederherstellen",
        aliases=("aufgabe wiederherstellen", "stelle aufgabe wieder her"),
        risk=ActionRisk.WRITE, requires_confirmation=True, requires_workspace=True,
        parameters={"task": {"type": "string", "minLength": 1}},
        handler=bound("tasks.restore"), capability_source="desktop_task_service",
    ))
    registry.register(ActionDefinition(
        id="calendar.create", title="Termin erstellen", aliases=("erstelle termin", "neuer termin"),
        risk=ActionRisk.EXTERNAL_WRITE, requires_approval=True, requires_workspace=True,
        parameters={"title": {"type": "string", "minLength": 1}, "when": {"type": "string", "minLength": 1}}, handler=bound("calendar.create"),
        capability_source="calendar_assistant",
    ))
    registry.register(ActionDefinition(
        id="mail.send", title="E-Mail senden", aliases=("sende antwort", "sende mail"),
        risk=ActionRisk.EXTERNAL_WRITE, requires_approval=True, requires_workspace=True,
        parameters={"recipient": {"type": "string", "minLength": 1}, "body": {"type": "string", "minLength": 1}}, handler=bound("mail.send"),
        capability_source="mail_assistant",
    ))
    registry.register(ActionDefinition(
        id="search.query", title="Wissen durchsuchen", aliases=("suche", "suche nach"),
        parameters={"query": {"type": "string", "minLength": 1}}, handler=bound("search.query"),
        capability_source="rag_chat_service",
    ))
    registry.register(ActionDefinition(
        id="index.repair", title="Vektorindex reparieren", aliases=("repariere index", "index reparieren"),
        risk=ActionRisk.WRITE, requires_confirmation=True,
        handler=bound("index.repair"), capability_source="vector_provider_guard",
    ))
    return registry
