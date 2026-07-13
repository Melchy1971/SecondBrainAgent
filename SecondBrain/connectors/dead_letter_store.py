"""Persistent dead-letter queue + replay. Extends the existing dead_letter model."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from secondbrain.connectors.dead_letter import DeadLetter


class JsonDeadLetterQueue:
    """Durable DLQ (JSON file). Implements the DeadLetterQueue protocol surface."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._letters: list[DeadLetter] = self._load()

    def _load(self) -> list[DeadLetter]:
        if not self.path.exists():
            return []
        raw = json.loads(self.path.read_text(encoding="utf-8") or "[]")
        return [DeadLetter(**{k: v for k, v in d.items()}) for d in raw]

    def _persist(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps([l.to_dict() for l in self._letters], indent=2), encoding="utf-8")

    def push(self, letter: DeadLetter) -> DeadLetter:
        self._letters.append(letter)
        self._persist()
        return letter

    def list(self, connector: str | None = None) -> list[DeadLetter]:
        if connector is None:
            return list(self._letters)
        return [l for l in self._letters if l.connector == connector]

    def clear(self, connector: str | None = None) -> int:
        before = len(self._letters)
        self._letters = [] if connector is None else [l for l in self._letters if l.connector != connector]
        self._persist()
        return before - len(self._letters)


def replay(queue, handler: Callable[[DeadLetter], bool], *, connector: str | None = None) -> dict:
    """Reprocess dead letters. handler returns True on success (letter removed).

    Failed replays stay in the queue with incremented attempts.
    """
    letters = queue.list(connector)
    succeeded, failed = 0, 0
    remaining: list[DeadLetter] = []
    for letter in letters:
        try:
            ok = bool(handler(letter))
        except Exception:
            ok = False
        if ok:
            succeeded += 1
        else:
            failed += 1
            remaining.append(DeadLetter(**{**letter.to_dict(), "attempts": letter.attempts + 1}))
    # rebuild queue: keep other-connector letters + failed replays
    queue.clear(connector)
    for letter in remaining:
        queue.push(letter)
    return {"replayed": len(letters), "succeeded": succeeded, "failed": failed}
