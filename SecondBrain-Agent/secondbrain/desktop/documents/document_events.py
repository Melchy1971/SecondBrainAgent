"""Document center events."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class DocumentEventType(str, Enum):
    DOCUMENT_ADDED = "DOCUMENT_ADDED"
    DOCUMENT_UPDATED = "DOCUMENT_UPDATED"
    DOCUMENT_DELETED = "DOCUMENT_DELETED"
    DOCUMENT_SELECTED = "DOCUMENT_SELECTED"
    DOCUMENT_REINDEXED = "DOCUMENT_REINDEXED"
    BULK_ACTION_EXECUTED = "BULK_ACTION_EXECUTED"


@dataclass(frozen=True)
class DocumentEvent:
    type: DocumentEventType
    document_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)


class DocumentEventBus:
    def __init__(self) -> None:
        self._subscribers: list[Callable[[DocumentEvent], None]] = []
        self.events: list[DocumentEvent] = []

    def subscribe(self, handler: Callable[[DocumentEvent], None]) -> None:
        self._subscribers.append(handler)

    def publish(self, event: DocumentEvent) -> None:
        self.events.append(event)
        for handler in list(self._subscribers):
            handler(event)
