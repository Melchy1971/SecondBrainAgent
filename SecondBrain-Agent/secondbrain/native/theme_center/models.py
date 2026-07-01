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
class ThemeToken:
    key: str
    value: str
    role: str = "color"

    def to_dict(self) -> dict[str, Any]:
        return {"key": self.key, "value": self.value, "role": self.role}


@dataclass(frozen=True)
class NativeTheme:
    id: str
    name: str
    mode: str
    description: str
    tokens: dict[str, str]
    typography: dict[str, str] = field(default_factory=dict)
    density: str = "comfortable"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "mode": self.mode,
            "description": self.description,
            "tokens": dict(self.tokens),
            "typography": dict(self.typography),
            "density": self.density,
        }


@dataclass(frozen=True)
class ThemeSnapshot:
    ok: bool
    version: str
    active_theme: str
    available_themes: list[NativeTheme]
    project_root: str
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "version": self.version,
            "active_theme": self.active_theme,
            "available_themes": [theme.to_dict() for theme in self.available_themes],
            "theme_count": len(self.available_themes),
            "project_root": self.project_root,
            "blockers": list(self.blockers),
        }
