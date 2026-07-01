from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

from .models import NotificationItem, NotificationSnapshot, VALID_CATEGORIES, VALID_LEVELS, normalize_project_root


class NotificationCenterService:
    """Native notification and event surface for the Jarvis desktop suite.

    The center stores append-only JSONL notifications and keeps read-state in a
    compact JSON file. This keeps the module dependency-free, testable and safe for
    startup diagnostics before databases or connectors are available.
    """

    VERSION = "v30.43"

    def __init__(self, project_root: str | Path = ".") -> None:
        self.project_root = normalize_project_root(project_root)
        self.runtime_dir = self.project_root / "runtime" / "native" / "notification_center"
        self.notifications_path = self.runtime_dir / "notifications.jsonl"
        self.read_state_path = self.runtime_dir / "read_state.json"

    def ensure_dirs(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)

    def _now(self) -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def _read_state(self) -> dict[str, bool]:
        self.ensure_dirs()
        if not self.read_state_path.exists():
            return {}
        try:
            data = json.loads(self.read_state_path.read_text(encoding="utf-8"))
            return {str(k): bool(v) for k, v in dict(data).items()}
        except Exception:
            return {}

    def _write_read_state(self, state: dict[str, bool]) -> None:
        self.ensure_dirs()
        self.read_state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    def _load_raw(self) -> list[dict[str, Any]]:
        self.ensure_dirs()
        if not self.notifications_path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in self.notifications_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                if isinstance(row, dict):
                    rows.append(row)
            except Exception:
                rows.append({
                    "id": f"invalid-{len(rows)+1}",
                    "ts": self._now(),
                    "level": "warning",
                    "category": "system",
                    "title": "Ungültige Benachrichtigung",
                    "message": line[:300],
                    "source": "notification_center",
                })
        return rows

    def list_items(self, limit: int = 50, unread_only: bool = False, category: str | None = None) -> dict[str, Any]:
        read_state = self._read_state()
        items: list[NotificationItem] = []
        for row in self._load_raw():
            item = NotificationItem.from_dict(row)
            read = bool(read_state.get(item.id, item.read))
            item = NotificationItem(**{**item.to_dict(), "read": read})
            if unread_only and item.read:
                continue
            if category and item.category != category:
                continue
            items.append(item)
        items = items[-max(1, int(limit)): ]
        items.reverse()
        return {"ok": True, "items": [item.to_dict() for item in items], "count": len(items)}

    def notify(
        self,
        title: str,
        message: str,
        level: str = "info",
        category: str = "system",
        source: str = "native",
        action_required: bool = False,
        actions: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.ensure_dirs()
        normalized_level = level if level in VALID_LEVELS else "info"
        normalized_category = category if category in VALID_CATEGORIES else "system"
        item = NotificationItem(
            id=str(uuid.uuid4()),
            ts=self._now(),
            level=normalized_level,
            category=normalized_category,
            title=title.strip() or "Benachrichtigung",
            message=message.strip(),
            source=source.strip() or "native",
            read=False,
            action_required=bool(action_required or normalized_level == "action_required"),
            actions=actions or [],
            metadata=metadata or {},
        )
        with self.notifications_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")
        return {"ok": True, "notification": item.to_dict()}

    def mark_read(self, notification_id: str) -> dict[str, Any]:
        state = self._read_state()
        ids = {item.get("id") for item in self._load_raw()}
        if notification_id not in ids:
            return {"ok": False, "error": "notification_not_found", "id": notification_id}
        state[notification_id] = True
        self._write_read_state(state)
        return {"ok": True, "id": notification_id, "read": True}

    def mark_all_read(self) -> dict[str, Any]:
        state = self._read_state()
        count = 0
        for row in self._load_raw():
            item_id = str(row.get("id") or "")
            if item_id:
                state[item_id] = True
                count += 1
        self._write_read_state(state)
        return {"ok": True, "marked_read": count}

    def clear(self, keep_unread: bool = False) -> dict[str, Any]:
        self.ensure_dirs()
        if not self.notifications_path.exists():
            return {"ok": True, "cleared": 0}
        if not keep_unread:
            count = len(self._load_raw())
            self.notifications_path.write_text("", encoding="utf-8")
            self._write_read_state({})
            return {"ok": True, "cleared": count}
        unread = [item for item in self.list_items(limit=100000, unread_only=True).get("items", [])]
        self.notifications_path.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in reversed(unread)), encoding="utf-8")
        self._write_read_state({})
        return {"ok": True, "cleared": "read", "kept_unread": len(unread)}

    def snapshot(self, limit: int = 8) -> NotificationSnapshot:
        items = [NotificationItem.from_dict(row) for row in self._load_raw()]
        read_state = self._read_state()
        normalized: list[NotificationItem] = []
        for item in items:
            normalized.append(NotificationItem(**{**item.to_dict(), "read": bool(read_state.get(item.id, item.read))}))
        by_level: dict[str, int] = {}
        by_category: dict[str, int] = {}
        for item in normalized:
            by_level[item.level] = by_level.get(item.level, 0) + 1
            by_category[item.category] = by_category.get(item.category, 0) + 1
        unread = sum(1 for item in normalized if not item.read)
        action_required = sum(1 for item in normalized if item.action_required and not item.read)
        blockers: list[str] = []
        if action_required:
            blockers.append("notifications_action_required")
        latest = list(reversed(normalized[-max(1, int(limit)):]))
        return NotificationSnapshot(
            ok=True,
            total=len(normalized),
            unread=unread,
            action_required=action_required,
            by_level=by_level,
            by_category=by_category,
            latest=latest,
            blockers=blockers,
        )

    def status(self) -> dict[str, Any]:
        data = self.snapshot().to_dict()
        data.update({
            "version": self.VERSION,
            "project_root": str(self.project_root),
            "runtime_dir": str(self.runtime_dir),
            "notification_file": str(self.notifications_path),
        })
        return data
