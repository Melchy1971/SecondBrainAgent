"""Status bar composition (workspace, connection, jobs, notifications, clock)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StatusBarModel:
    workspace: str = "default"
    connection: str = "offline"          # online | offline | degraded
    active_jobs: int = 0
    unread_notifications: int = 0
    message: str = ""

    def segments(self) -> list[dict]:
        segs = [
            {"id": "workspace", "text": f"⌂ {self.workspace}", "role": "info"},
            {"id": "connection", "text": self.connection,
             "role": {"online": "success", "degraded": "warning", "offline": "error"}.get(self.connection, "fg_muted")},
        ]
        if self.active_jobs:
            segs.append({"id": "jobs", "text": f"⚙ {self.active_jobs} jobs", "role": "info"})
        if self.unread_notifications:
            segs.append({"id": "notifications", "text": f"● {self.unread_notifications}", "role": "warning"})
        if self.message:
            segs.append({"id": "message", "text": self.message, "role": "fg_muted"})
        return segs
