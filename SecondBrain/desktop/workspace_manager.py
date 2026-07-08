from __future__ import annotations

from pathlib import Path

from .workspaces.workspace_registry import WorkspaceRegistry
from .workspaces.workspace_state import WorkspaceRef
from .workspaces.workspace_store import WorkspaceStore


class WorkspaceManager:
    """Desktop-facing multi-workspace facade."""

    def __init__(self, config_dir: str | Path = ".config/secondbrain") -> None:
        self.config_dir = Path(config_dir)
        self.registry = WorkspaceRegistry(
            WorkspaceStore(self.config_dir / "workspaces.json"),
            default_root=self.config_dir / "workspaces" / "default",
        )

    def current_workspace(self) -> WorkspaceRef:
        return self.registry.active()

    def list_workspaces(self) -> list[WorkspaceRef]:
        return self.registry.list_workspaces()

    def create_workspace(self, workspace_id: str, name: str, root_path: str | Path, *, activate: bool = True) -> WorkspaceRef:
        return self.registry.add_workspace(
            WorkspaceRef(workspace_id=workspace_id, name=name, root_path=str(root_path)),
            activate=activate,
        )

    def switch_workspace(self, workspace_id: str) -> WorkspaceRef:
        return self.registry.switch(workspace_id)

    def delete_workspace(self, workspace_id: str) -> None:
        self.registry.remove(workspace_id)

    def workspace_path(self, *parts: str) -> Path:
        return Path(self.current_workspace().root_path).joinpath(*parts)

# Backward compatible aliases for P2.1.1 desktop imports.
Workspace = WorkspaceRef


def _legacy_create(self: WorkspaceManager, name: str) -> WorkspaceRef:
    workspace_id = name.strip().lower().replace(" ", "-") or "workspace"
    candidate = workspace_id
    suffix = 2
    existing = {item.workspace_id for item in self.list_workspaces()}
    while candidate in existing:
        candidate = f"{workspace_id}-{suffix}"
        suffix += 1
    created = self.create_workspace(candidate, name, self.config_dir / "workspaces" / candidate)
    legacy_created = getattr(self, "_legacy_created_workspace_ids", set())
    legacy_created.add(created.workspace_id)
    self._legacy_created_workspace_ids = legacy_created
    return created


def _legacy_get(self: WorkspaceManager, workspace_id: str) -> WorkspaceRef | None:
    try:
        return self.registry.get(workspace_id)
    except KeyError:
        return None


def _legacy_list(self: WorkspaceManager) -> list[WorkspaceRef]:
    legacy_created = getattr(self, "_legacy_created_workspace_ids", None)
    if legacy_created is not None:
        return [workspace for workspace in self.list_workspaces() if workspace.workspace_id in legacy_created]
    return [workspace for workspace in self.list_workspaces() if not workspace.is_default]


WorkspaceManager.create = _legacy_create  # type: ignore[attr-defined]
WorkspaceManager.get = _legacy_get  # type: ignore[attr-defined]
WorkspaceManager.list = _legacy_list  # type: ignore[attr-defined]
