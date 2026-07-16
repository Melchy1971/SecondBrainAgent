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

__all__ = ["CardArea", "CardStatus", "CardItem", "DashboardCard", "DashboardConfig", "DashboardSnapshot", "DEFAULT_CARD_ORDER"]


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
    summary: str = ""
    source: str = ""
    updated_at: str = ""
    deep_link: str = ""
    error_state: str = ""
    cached: bool = False

    @property
    def card_type(self) -> str:
        return self.card_id

    @property
    def is_cached(self) -> bool:
        return self.cached

    @property
    def visible_items(self) -> list[CardItem]:
        return list(self.items)

    def to_dict(self) -> dict[str, Any]:
        return {"card_id": self.card_id, "card_type": self.card_type,
                "title": self.title, "area": self.area,
                "status": self.status, "items": [i.to_dict() for i in self.items],
                "error": self.error, "error_state": self.error_state, "priority": self.priority,
                "summary": self.summary, "source": self.source, "updated_at": self.updated_at,
                "deep_link": self.deep_link, "cached": self.cached, "is_cached": self.is_cached}


@dataclass
class DashboardConfig:
    enabled: list[str] = field(default_factory=list)
    order: list[str] = field(default_factory=list)
    timeframe: str = "today"     # today | week | custom
    workspace_id: str = ""
    density: str = "comfortable"
    preferred_home: str = "dashboard"

    def to_dict(self) -> dict[str, Any]:
        return {"enabled": list(self.enabled), "order": list(self.order),
                "timeframe": self.timeframe, "workspace_id": self.workspace_id,
                "density": self.density, "preferred_home": self.preferred_home}


@dataclass
class DashboardSnapshot:
    workspace: str
    generated_at: str
    cards: list[DashboardCard] = field(default_factory=list)
    source_status: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        by_id = {card.card_id: card.to_dict() for card in self.cards}
        return {"workspace": self.workspace, "generated_at": self.generated_at,
                "today": by_id.get("next_up", {}), "tasks": by_id.get("tasks", {}),
                "calendar": by_id.get("calendar", {}), "mail": by_id.get("important_mail", {}),
                "projects": by_id.get("projects", {}), "approvals": by_id.get("open_approvals", {}),
                "reviews": by_id.get("reviews", {}),
                "suggestions": by_id.get("suggestions", {}), "documents": by_id.get("documents", {}),
                "knowledge": by_id.get("knowledge", {}), "jobs": by_id.get("jobs", {}),
                "system_health": by_id.get("system", {}),
                "source_status": dict(self.source_status)}


DEFAULT_CARD_ORDER: tuple[str, ...] = (
    "next_up", "open_approvals", "tasks", "calendar", "important_mail",
    "projects", "reviews", "suggestions", "documents", "knowledge", "jobs", "system", "recent_activity",
)
