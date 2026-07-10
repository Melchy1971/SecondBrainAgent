"""Append-only vault audit trail.

Records vault operations (create/read/update/delete/rotate/import/export) with
workspace, secret name, key version, actor, and timestamp. It never records
secret values.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class VaultAudit:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def record(
        self,
        action: str,
        *,
        workspace: str | None = None,
        name: str | None = None,
        key_version: int | None = None,
        actor: str = "system",
        detail: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "workspace": workspace,
            "name": name,
            "key_version": key_version,
            "actor": actor,
            "detail": detail or {},
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
        return entry

    def entries(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        out: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                out.append(json.loads(line))
        return out
