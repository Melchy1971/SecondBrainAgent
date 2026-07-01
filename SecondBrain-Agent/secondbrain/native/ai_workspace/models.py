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
class WorkspaceModuleState:
    id: str
    title: str
    status: str
    command: str
    summary: str
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "command": self.command,
            "summary": self.summary,
            "blockers": self.blockers,
        }


@dataclass(frozen=True)
class WorkspaceSnapshot:
    ok: bool
    version: str
    project_root: str
    primary_surface: str
    modules: list[WorkspaceModuleState]
    activity_count: int = 0
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "version": self.version,
            "project_root": self.project_root,
            "primary_surface": self.primary_surface,
            "modules": [module.to_dict() for module in self.modules],
            "activity_count": self.activity_count,
            "blockers": self.blockers,
        }
