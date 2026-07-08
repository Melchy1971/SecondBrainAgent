from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

HIGH_RISK_ACTIONS = {
    "delete_documents",
    "delete_workspace",
    "execute_shell",
    "export_sensitive_data",
}


@dataclass
class ApprovalRequest:
    request_id: str
    task_id: str
    reason: str
    status: str = "PENDING"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


class ApprovalManager:
    def __init__(self) -> None:
        self.requests: dict[str, ApprovalRequest] = {}

    def requires_approval(self, tool_calls: list[str], metadata: dict[str, Any] | None = None) -> bool:
        metadata = metadata or {}
        if any(call in HIGH_RISK_ACTIONS for call in tool_calls):
            return True
        if metadata.get("bulk_items", 0) > 100:
            return True
        return False

    def request(self, task_id: str, reason: str, metadata: dict[str, Any] | None = None) -> ApprovalRequest:
        request_id = f"approval:{task_id}"
        approval = ApprovalRequest(request_id=request_id, task_id=task_id, reason=reason, metadata=metadata or {})
        self.requests[request_id] = approval
        return approval

    def decide(self, request_id: str, granted: bool) -> ApprovalRequest:
        approval = self.requests[request_id]
        approval.status = "GRANTED" if granted else "DENIED"
        return approval

    def granted_for(self, task_id: str) -> bool:
        return any(req.task_id == task_id and req.status == "GRANTED" for req in self.requests.values())
