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
class PanelSpec:
    id: str
    title: str
    module: str
    region: str
    visible: bool = True
    weight: int = 1
    command: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "module": self.module,
            "region": self.region,
            "visible": self.visible,
            "weight": self.weight,
            "command": self.command,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PanelSpec":
        return cls(
            id=str(data.get("id") or data.get("module") or "panel"),
            title=str(data.get("title") or data.get("id") or "Panel"),
            module=str(data.get("module") or data.get("id") or "unknown"),
            region=str(data.get("region") or "center"),
            visible=bool(data.get("visible", True)),
            weight=int(data.get("weight", 1) or 1),
            command=data.get("command"),
        )


@dataclass(frozen=True)
class LayoutSpec:
    name: str
    title: str
    description: str
    version: str = "v30.41"
    left_width: int = 260
    right_width: int = 340
    bottom_height: int = 180
    panels: list[PanelSpec] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "version": self.version,
            "left_width": self.left_width,
            "right_width": self.right_width,
            "bottom_height": self.bottom_height,
            "panels": [panel.to_dict() for panel in self.panels],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LayoutSpec":
        return cls(
            name=str(data.get("name") or "default"),
            title=str(data.get("title") or data.get("name") or "Standard"),
            description=str(data.get("description") or ""),
            version=str(data.get("version") or "v30.41"),
            left_width=int(data.get("left_width", 260) or 260),
            right_width=int(data.get("right_width", 340) or 340),
            bottom_height=int(data.get("bottom_height", 180) or 180),
            panels=[PanelSpec.from_dict(row) for row in data.get("panels", []) if isinstance(row, dict)],
        )
