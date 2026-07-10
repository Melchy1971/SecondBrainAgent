"""P5 v23.0 - Approval Inbox."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class ApprovalInbox:
    def __init__(self, project_root: str | Path = ".", *, safety: Any | None = None):
        from secondbrain.agent.safety import SafetyService

        self.project_root = Path(project_root).resolve()
        self.safety = safety or SafetyService(self.project_root)

    def pending_items(self) -> list[dict[str, Any]]:
        rows = self.safety.list()
        items = [row for row in rows if row.get("status") in {"pending", "deferred"}]
        return sorted(items, key=lambda row: str(row.get("created_at", "")), reverse=True)

    def approve(self, approval_id: str, *, decided_by: str = "user") -> dict[str, Any]:
        return self.safety.approve(approval_id, decided_by=decided_by).to_dict()

    def reject(self, approval_id: str, *, decided_by: str = "user") -> dict[str, Any]:
        return self.safety.reject(approval_id, decided_by=decided_by).to_dict()

    def defer(
        self,
        approval_id: str,
        *,
        decided_by: str = "user",
        until: str = "",
        note: str = "",
    ) -> dict[str, Any]:
        return self.safety.defer(approval_id, decided_by=decided_by, until=until, note=note).to_dict()

    def render(self, approvals: list[dict] | None = None) -> dict[str, Any]:
        items = approvals if approvals is not None else self.pending_items()
        pending = [row for row in items if row.get("status") == "pending"]
        deferred = [row for row in items if row.get("status") == "deferred"]
        return {
            "pending": len(pending),
            "deferred": len(deferred),
            "items": items,
            "actions": ["approve", "reject", "defer"],
        }
