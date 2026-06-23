from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class DesktopState:
    selected_workspace: str | None = None
    selected_view: str = "dashboard"
    sidebar_collapsed: bool = False
    open_tabs: list[str] = field(default_factory=list)
    active_jobs: list[str] = field(default_factory=list)
    notifications: list[str] = field(default_factory=list)
    window_geometry: str = "1200x800"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "DesktopState":
        if not data:
            return cls()
        allowed = {field.name for field in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        clean = {key: value for key, value in data.items() if key in allowed}
        return cls(**clean)


class DesktopStateStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> DesktopState:
        if not self.path.exists():
            return DesktopState()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return DesktopState()
        if not isinstance(payload, dict):
            return DesktopState()
        return DesktopState.from_dict(payload)

    def save(self, state: DesktopState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(state.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
