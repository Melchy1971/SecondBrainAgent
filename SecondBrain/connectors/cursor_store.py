"""P1.2.1 - Cursor repositories for connector sync."""

from __future__ import annotations

import json
from pathlib import Path
from threading import RLock
from typing import Protocol

from .sync_state import SyncCursor


class CursorStore(Protocol):
    def get(self, connector: str) -> SyncCursor | None: ...
    def save(self, cursor: SyncCursor) -> None: ...
    def delete(self, connector: str) -> None: ...


class InMemoryCursorStore:
    def __init__(self) -> None:
        self._items: dict[str, SyncCursor] = {}
        self._lock = RLock()

    def get(self, connector: str) -> SyncCursor | None:
        with self._lock:
            return self._items.get(connector)

    def save(self, cursor: SyncCursor) -> None:
        with self._lock:
            self._items[cursor.connector] = cursor

    def delete(self, connector: str) -> None:
        with self._lock:
            self._items.pop(connector, None)


class JsonCursorStore:
    """Small durable cursor store.

    Intended for local/dev/runtime use. Production deployments can replace it
    with a DB-backed implementation behind the same CursorStore protocol.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lock = RLock()

    def get(self, connector: str) -> SyncCursor | None:
        with self._lock:
            data = self._read_all()
            raw = data.get(connector)
            return SyncCursor.from_dict(raw) if raw else None

    def save(self, cursor: SyncCursor) -> None:
        with self._lock:
            data = self._read_all()
            data[cursor.connector] = cursor.to_dict()
            self._write_all(data)

    def delete(self, connector: str) -> None:
        with self._lock:
            data = self._read_all()
            if connector in data:
                del data[connector]
                self._write_all(data)

    def _read_all(self) -> dict[str, dict]:
        if not self.path.exists():
            return {}
        text = self.path.read_text(encoding="utf-8").strip()
        if not text:
            return {}
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise ValueError("Cursor store must contain a JSON object")
        return payload

    def _write_all(self, data: dict[str, dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self.path)
