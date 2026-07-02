from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
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


@dataclass
class ApplicationState:
    """UI-independent state shared by the native desktop shell components."""

    project_root: str
    version: str
    modules: list[WorkspaceModuleState]
    active_module: str = "dashboard"
    status: str = "initializing"
    message: str = "Desktop wird initialisiert"
    last_updated: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def select_module(self, module_id: str) -> WorkspaceModuleState:
        module = next((item for item in self.modules if item.id == module_id), None)
        if module is None:
            raise KeyError(f"unknown desktop module: {module_id}")
        if module.status != "ready":
            raise ValueError(f"desktop module is unavailable: {module_id}")
        self.active_module = module_id
        self.status = "ready"
        self.message = f"{module.title} geoeffnet"
        self.touch()
        return module

    def replace_modules(self, modules: list[WorkspaceModuleState]) -> None:
        self.modules = list(modules)
        ready_ids = {item.id for item in modules if item.status == "ready"}
        if self.active_module not in ready_ids:
            self.active_module = "dashboard" if "dashboard" in ready_ids else next(iter(ready_ids), "")
        self.status = "ready" if all(item.status == "ready" for item in modules) else "degraded"
        self.message = f"{len(ready_ids)}/{len(modules)} Module verfuegbar"
        self.touch()

    def set_error(self, message: str) -> None:
        self.status = "error"
        self.message = message
        self.touch()

    def touch(self) -> None:
        self.last_updated = datetime.now(UTC).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_root": self.project_root,
            "version": self.version,
            "active_module": self.active_module,
            "status": self.status,
            "message": self.message,
            "last_updated": self.last_updated,
            "modules": [module.to_dict() for module in self.modules],
        }
