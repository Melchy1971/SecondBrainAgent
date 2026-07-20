from __future__ import annotations

from typing import Any

from secondbrain.native.approval import NativeApprovalQueue


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
