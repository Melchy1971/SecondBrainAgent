from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ToolAuditEntry:
    tool_name: str
    caller: str
    success: bool
    arguments: dict[str, Any]
    error: str | None = None
    correlation_id: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ToolAuditLog:
    entries: list[ToolAuditEntry] = field(default_factory=list)

    def record(self, entry: ToolAuditEntry) -> None:
        self.entries.append(entry)

    def last(self) -> ToolAuditEntry | None:
        return self.entries[-1] if self.entries else None
