"""P1.2.1 - Connector sync state primitives.

This module keeps connector progress explicit and serialisable. It is intentionally
framework-neutral so Gmail/Drive/GitHub/etc. adapters can use the same cursor and
failure model without depending on external services during tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SyncStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True)
class SyncCursor:
    connector: str
    value: str | None = None
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {"connector": self.connector, "value": self.value, "updated_at": self.updated_at}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SyncCursor":
        return cls(
            connector=str(data["connector"]),
            value=None if data.get("value") is None else str(data.get("value")),
            updated_at=str(data.get("updated_at") or utc_now_iso()),
        )


@dataclass(frozen=True)
class SyncIssue:
    item_id: str | None
    code: str
    message: str
    fatal: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {"item_id": self.item_id, "code": self.code, "message": self.message, "fatal": self.fatal}


@dataclass
class SyncRunResult:
    connector: str
    status: SyncStatus
    cursor_before: str | None
    cursor_after: str | None
    fetched: int = 0
    processed: int = 0
    skipped: int = 0
    failed: int = 0
    issues: list[SyncIssue] = field(default_factory=list)
    started_at: str = field(default_factory=utc_now_iso)
    finished_at: str | None = None

    @property
    def ok(self) -> bool:
        return self.status in {SyncStatus.SUCCESS, SyncStatus.PARTIAL}

    def finish(self, status: SyncStatus) -> "SyncRunResult":
        self.status = status
        self.finished_at = utc_now_iso()
        return self

    def add_issue(self, issue: SyncIssue) -> None:
        self.issues.append(issue)
        self.failed += 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "connector": self.connector,
            "status": self.status.value,
            "cursor_before": self.cursor_before,
            "cursor_after": self.cursor_after,
            "fetched": self.fetched,
            "processed": self.processed,
            "skipped": self.skipped,
            "failed": self.failed,
            "issues": [issue.to_dict() for issue in self.issues],
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "ok": self.ok,
        }
