from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4


class NotificationLevel(StrEnum):
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class Notification:
    title: str
    message: str
    level: NotificationLevel = NotificationLevel.INFO
    id: str = field(default_factory=lambda: uuid4().hex)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    read: bool = False


class NotificationCenter:
    def __init__(self) -> None:
        self._items: list[Notification] = []

    def push(self, title: str, message: str, level: NotificationLevel = NotificationLevel.INFO) -> Notification:
        item = Notification(title=title, message=message, level=level)
        self._items.append(item)
        return item

    def list(self, unread_only: bool = False) -> list[Notification]:
        if unread_only:
            return [item for item in self._items if not item.read]
        return list(self._items)

    def clear(self) -> None:
        self._items.clear()
