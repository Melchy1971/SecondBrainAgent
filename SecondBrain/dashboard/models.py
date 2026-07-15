"""Data model for the personal Jarvis dashboard.

A dashboard is a set of independent cards. Each card owns its own status and
error state so one broken source can never blank the whole surface. Card items
carry a human label and an opaque ``reference`` for drill-down - never a
technical id in the visible label, and never a sensitive preview.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

__all__ = ["CardArea", "CardStatus", "CardItem", "DashboardCard", "DashboardConfig", "DEFAULT_CARD_ORDER"]


class CardArea(StrEnum):
    HEUTE = "heute"
    ARBEIT = "arbeit"
    KOMMUNIKATION = "kommunikation"
    ENTSCHEIDUNGEN = "entscheidungen"
    WISSEN = "wissen"
    SYSTEM = "system"


class CardStatus(StrEnum):
    OK = "ok"
    EMPTY = "empty"
    LOADING = "loading"          # slow source deferred to async
    ERROR = "error"              # source failed - card isolated


@dataclass
class CardItem:
    label: str
    reference: str = ""          # opaque back-link for drill-down, not shown as id
    detail: str = ""
    badge: str = ""
    approval_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {"label": self.label, "reference": self.reference, "detail": self.detail,
                "badge": self.badge, "approval_required": self.approval_required}


@dataclass
class DashboardCard:
    card_id: str
    title: str
    area: str
    status: str = CardStatus.OK.value
    items: list[CardItem] = field(default_factory=list)
    error: str = ""
    priority: int = 0

    @property
    def visible_items(self) -> list[CardItem]:
        return list(self.items)

    def to_dict(self) -> dict[str, Any]:
        return {"card_id": self.card_id, "title": self.title, "area": self.area,
                "status": self.status, "items": [i.to_dict() for i in self.items],
                "error": self.error, "priority": self.priority}


@dataclass
class DashboardConfig:
    enabled: list[str] = field(default_factory=list)
    order: list[str] = field(default_factory=list)
    timeframe: str = "today"     # today | week | custom
    workspace_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"enabled": list(self.enabled), "order": list(self.order),
                "timeframe": self.timeframe, "workspace_id": self.workspace_id}


DEFAULT_CARD_ORDER: tuple[str, ...] = (
    "next_up", "open_approvals", "tasks", "calendar", "important_mail",
    "projects", "suggestions", "documents", "knowledge", "system", "recent_activity",
)
