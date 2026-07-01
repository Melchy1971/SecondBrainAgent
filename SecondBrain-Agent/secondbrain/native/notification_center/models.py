from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def normalize_project_root(project_root: str | Path) -> Path:
    root = Path(project_root).resolve()
    if (root / "SecondBrain-Agent").exists() and not (root / "launcher.py").exists():
        return root / "SecondBrain-Agent"
    return root


VALID_LEVELS = {"info", "success", "warning", "error", "action_required"}
VALID_CATEGORIES = {"system", "rag", "documents", "memory", "agent", "voice", "security", "update", "installer", "user"}


@dataclass(frozen=True)
class NotificationItem:
    id: str
    ts: str
    level: str
    category: str
    title: str
    message: str
    source: str = "native"
    read: bool = False
    action_required: bool = False
    actions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "ts": self.ts,
            "level": self.level,
            "category": self.category,
            "title": self.title,
            "message": self.message,
            "source": self.source,
            "read": self.read,
            "action_required": self.action_required,
            "actions": list(self.actions),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NotificationItem":
        level = str(data.get("level") or "info")
        category = str(data.get("category") or "system")
        return cls(
            id=str(data.get("id") or ""),
            ts=str(data.get("ts") or ""),
            level=level if level in VALID_LEVELS else "info",
            category=category if category in VALID_CATEGORIES else "system",
            title=str(data.get("title") or ""),
            message=str(data.get("message") or ""),
            source=str(data.get("source") or "native"),
            read=bool(data.get("read", False)),
            action_required=bool(data.get("action_required", False)),
            actions=[str(item) for item in data.get("actions", []) if str(item).strip()],
            metadata=dict(data.get("metadata") or {}),
        )


@dataclass(frozen=True)
class NotificationSnapshot:
    ok: bool
    total: int
    unread: int
    action_required: int
    by_level: dict[str, int]
    by_category: dict[str, int]
    latest: list[NotificationItem]
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "total": self.total,
            "unread": self.unread,
            "action_required": self.action_required,
            "by_level": dict(self.by_level),
            "by_category": dict(self.by_category),
            "latest": [item.to_dict() for item in self.latest],
            "blockers": list(self.blockers),
        }
