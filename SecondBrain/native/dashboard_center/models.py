from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def normalize_project_root(project_root: str | Path) -> Path:
    root = Path(project_root).resolve()
    if (root / "SecondBrain-Agent").exists() and not (root / "launcher.py").exists():
        return root / "SecondBrain-Agent"
    return root


@dataclass(frozen=True)
class DashboardCard:
    id: str
    title: str
    status: str
    value: Any
    description: str
    command: str | None = None
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "value": self.value,
            "description": self.description,
            "command": self.command,
            "blockers": self.blockers,
            "warnings": self.warnings,
        }


@dataclass(frozen=True)
class DashboardSnapshot:
    ok: bool
    version: str
    project_root: str
    surface: str
    cards: list[DashboardCard]
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    activity_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "version": self.version,
            "project_root": self.project_root,
            "surface": self.surface,
            "cards": [card.to_dict() for card in self.cards],
            "blockers": self.blockers,
            "warnings": self.warnings,
            "activity_count": self.activity_count,
        }
