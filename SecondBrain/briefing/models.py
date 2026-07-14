"""Data model for consolidated daily and weekly briefings.

A briefing is a list of :class:`BriefingSection` objects. Every displayed
statement carries a source reference and a confidence; uncertain statements are
marked so the reader never mistakes a guess for a fact. No field here holds a
technical identifier meant for display - ``source_reference`` is an opaque
back-link the GUI resolves on drill-down, not shown in overview text.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

__all__ = ["Priority", "SectionStatus", "BriefingKind", "BriefingItem", "BriefingSection", "Briefing"]


class Priority(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Numeric weight for ordering (higher == earlier).
PRIORITY_WEIGHT: dict[str, int] = {
    Priority.CRITICAL.value: 3,
    Priority.HIGH.value: 2,
    Priority.MEDIUM.value: 1,
    Priority.LOW.value: 0,
}


class SectionStatus(StrEnum):
    OK = "ok"
    EMPTY = "empty"
    CONNECTOR_ERROR = "connector_error"
    UNCERTAIN = "uncertain"


class BriefingKind(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"


@dataclass
class BriefingItem:
    text: str
    source_reference: str = ""
    source: str = ""
    confidence: float = 1.0
    uncertain: bool = False
    hidden: bool = False
    kind: str = ""              # semantic sub-type, e.g. "event", "task", "approval"
    due: str = ""
    preparation: list[str] = field(default_factory=list)  # references only

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "source_reference": self.source_reference,
            "source": self.source,
            "confidence": round(float(self.confidence), 3),
            "uncertain": bool(self.uncertain),
            "hidden": bool(self.hidden),
            "kind": self.kind,
            "due": self.due,
            "preparation": list(self.preparation),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BriefingItem":
        return cls(
            text=data.get("text", ""),
            source_reference=data.get("source_reference", ""),
            source=data.get("source", ""),
            confidence=float(data.get("confidence", 1.0)),
            uncertain=bool(data.get("uncertain", False)),
            hidden=bool(data.get("hidden", False)),
            kind=data.get("kind", ""),
            due=data.get("due", ""),
            preparation=list(data.get("preparation", [])),
        )


@dataclass
class BriefingSection:
    section_id: str
    title: str
    priority: str
    source: str
    items: list[BriefingItem] = field(default_factory=list)
    generated_at: str = ""
    confidence: float = 1.0
    status: str = SectionStatus.OK.value

    @property
    def visible_items(self) -> list[BriefingItem]:
        return [i for i in self.items if not i.hidden]

    def to_dict(self) -> dict[str, Any]:
        return {
            "section_id": self.section_id,
            "title": self.title,
            "priority": self.priority,
            "source": self.source,
            "items": [i.to_dict() for i in self.items],
            "generated_at": self.generated_at,
            "confidence": round(float(self.confidence), 3),
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BriefingSection":
        return cls(
            section_id=data.get("section_id", ""),
            title=data.get("title", ""),
            priority=data.get("priority", Priority.MEDIUM.value),
            source=data.get("source", ""),
            items=[BriefingItem.from_dict(i) for i in data.get("items", [])],
            generated_at=data.get("generated_at", ""),
            confidence=float(data.get("confidence", 1.0)),
            status=data.get("status", SectionStatus.OK.value),
        )


@dataclass
class Briefing:
    kind: str
    workspace_id: str
    generated_at: str
    sections: list[BriefingSection] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "workspace_id": self.workspace_id,
            "generated_at": self.generated_at,
            "sections": [s.to_dict() for s in self.sections],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Briefing":
        return cls(
            kind=data.get("kind", BriefingKind.DAILY.value),
            workspace_id=data.get("workspace_id", ""),
            generated_at=data.get("generated_at", ""),
            sections=[BriefingSection.from_dict(s) for s in data.get("sections", [])],
        )
