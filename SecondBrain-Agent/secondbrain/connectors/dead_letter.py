"""P1.2.2 - Dead-letter queue for connector sync failures.

Dead letters capture failed records without stopping the whole connector sync.
The queue abstraction is intentionally small so it can be backed by memory,
SQLite, Postgres, files, or an external queue later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class DeadLetter:
    connector: str
    code: str
    message: str
    item_id: str | None = None
    payload: Any = None
    cursor: str | None = None
    attempts: int = 1
    id: str = field(default_factory=lambda: uuid4().hex)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "connector": self.connector,
            "item_id": self.item_id,
            "cursor": self.cursor,
            "code": self.code,
            "message": self.message,
            "payload": self.payload,
            "attempts": self.attempts,
            "created_at": self.created_at,
        }


class DeadLetterQueue(Protocol):
    def push(self, letter: DeadLetter) -> DeadLetter: ...
    def list(self, connector: str | None = None) -> list[DeadLetter]: ...
    def clear(self, connector: str | None = None) -> int: ...


class InMemoryDeadLetterQueue:
    def __init__(self) -> None:
        self._letters: list[DeadLetter] = []

    def push(self, letter: DeadLetter) -> DeadLetter:
        self._letters.append(letter)
        return letter

    def list(self, connector: str | None = None) -> list[DeadLetter]:
        if connector is None:
            return list(self._letters)
        return [letter for letter in self._letters if letter.connector == connector]

    def clear(self, connector: str | None = None) -> int:
        before = len(self._letters)
        if connector is None:
            self._letters.clear()
            return before
        self._letters = [letter for letter in self._letters if letter.connector != connector]
        return before - len(self._letters)
