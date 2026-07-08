"""Persistent import history (append-only JSON)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ImportHistoryStore:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else None
        self._records: list[dict] = self._load()

    def _load(self) -> list[dict]:
        if self.path and self.path.exists():
            text = self.path.read_text(encoding="utf-8").strip()
            return json.loads(text) if text else []
        return []

    def record(self, *, path: str, status: str, doc_id: str | None = None,
               detail: dict[str, Any] | None = None) -> dict:
        entry = {"timestamp": datetime.now(timezone.utc).isoformat(), "path": path,
                 "status": status, "doc_id": doc_id, "detail": detail or {}}
        self._records.append(entry)
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self._records, indent=2), encoding="utf-8")
        return entry

    def all(self) -> list[dict]:
        return list(self._records)

    def recent(self, limit: int = 20) -> list[dict]:
        return list(reversed(self._records[-limit:]))

    def by_status(self, status: str) -> list[dict]:
        return [r for r in self._records if r["status"] == status]
