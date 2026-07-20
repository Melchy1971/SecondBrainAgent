from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from secondbrain.native.approval import NativeApprovalQueue

ELEVATED_RISK_LEVELS = {"external_write", "destructive", "privileged"}
APPROVAL_OVERDUE_AFTER = timedelta(minutes=15)


def approval_notification(previous: int | None, current: int) -> str | None:
    current = max(0, int(current))
    if previous is None:
        return None
    added = current - max(0, int(previous))
    if added <= 0:
        return None
    noun = "Freigabe wartet" if added == 1 else "Freigaben warten"
    return f"{added} neue {noun} auf Entscheidung."


def _created_at(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def approval_activity(snapshot: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    try:
        pending = max(0, int(snapshot["pending_count"]))
    except (TypeError, ValueError):
        return {
            "available": False,
            "pending": 0,
            "elevated": 0,
            "overdue": 0,
            "severity": "unavailable",
            "label": "Unavailable",
        }
    except KeyError:
        return {
            "available": False,
            "pending": 0,
            "elevated": 0,
            "overdue": 0,
            "severity": "unavailable",
            "label": "Unavailable",
        }
    items = snapshot.get("items")
    safe_items = items if isinstance(items, list) else []
    elevated = sum(
        1
        for item in safe_items
        if isinstance(item, dict) and str(item.get("risk_level", "")).casefold() in ELEVATED_RISK_LEVELS
    )
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    else:
        current = current.astimezone(timezone.utc)
    overdue = sum(
        1
        for item in safe_items
        if isinstance(item, dict)
        and (created := _created_at(item.get("created_at"))) is not None
        and current - created >= APPROVAL_OVERDUE_AFTER
    )
    label = f"{pending} Pending"
    if elevated:
        label += f" / {elevated} Elevated"
    if overdue:
        label += f" / {overdue} Overdue"
    severity = "critical" if overdue else "warning" if pending else "normal"
    return {
        "available": True,
        "pending": pending,
        "elevated": elevated,
        "overdue": overdue,
        "severity": severity,
        "label": label,
    }


class ApprovalSurface:
    """Workspace-isolated, payload-free projection for unprivileged desktop display."""

    def __init__(self, queue: NativeApprovalQueue, *, workspace_id: str, limit: int = 100) -> None:
        self.queue = queue
        self.workspace_id = workspace_id
        self.limit = max(1, min(int(limit), 500))

    def snapshot(self) -> dict[str, Any]:
        rows = [
            row
            for row in self.queue.list(status="pending")
            if str(row.get("workspace_id") or "") == self.workspace_id
        ]
        items = [self._safe_item(row) for row in reversed(rows[-self.limit :])]
        return {
            "status": "ready",
            "pending_count": len(rows),
            "visible_count": len(items),
            "items": items,
            "payloads_exposed": False,
            "workspace_isolated": True,
        }

    @staticmethod
    def _safe_item(row: dict[str, Any]) -> dict[str, str]:
        return {
            "approval_id": str(row.get("approval_id") or ""),
            "created_at": str(row.get("created_at") or ""),
            "action": str(row.get("command") or row.get("intent") or ""),
            "target": str(row.get("target") or ""),
            "risk_level": str(row.get("risk_level") or ""),
            "reason": str(row.get("reason") or ""),
            "status": "pending",
        }
