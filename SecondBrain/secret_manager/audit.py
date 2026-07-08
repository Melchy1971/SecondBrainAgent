"""Append-only audit log for secret operations. Never records secret values."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# actions that are permitted to be recorded; values are NEVER included
ACTIONS = {"unlock", "lock", "set", "get", "delete", "rotate_secret",
           "change_password", "rotate_master_key", "export", "import", "create"}


class AuditLog:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else None
        self._events: list[dict] = []

    def record(self, action: str, *, name: str | None = None, secret_type: str | None = None,
               actor: str = "system", ok: bool = True, detail: dict[str, Any] | None = None) -> dict:
        safe_detail = {k: v for k, v in (detail or {}).items()
                       if k not in {"value", "secret", "token", "password", "plaintext"}}
        event = {"timestamp": datetime.now(timezone.utc).isoformat(), "action": action,
                 "name": name, "type": secret_type, "actor": actor, "ok": ok, "detail": safe_detail}
        self._events.append(event)
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(event) + "\n")
        return event

    def events(self) -> list[dict]:
        return list(self._events)
