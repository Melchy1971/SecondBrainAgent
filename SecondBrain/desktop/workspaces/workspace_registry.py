from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .workspace_state import WorkspaceRef, WorkspaceRegistrySnapshot
from .workspace_store import WorkspaceStore


class WorkspaceNotFoundError(KeyError):
    pass


class DuplicateWorkspaceError(ValueError):
    pass


class WorkspaceRegistry:
    def __init__(self, store: WorkspaceStore, *, default_root: str | Path | None = None) -> None:
        self.store = store
        self.default_root = Path(default_root or ".secondbrain/workspaces/default")
        self._snapshot = store.load()
        if not self._snapshot.workspaces:
            self.add_workspace(
                WorkspaceRef(
                    workspace_id="default",
                    name="Default",
                    root_path=str(self.default_root),
                    is_default=True,
                ),
                activate=True,
                persist=False,
            )
            self.save()

    @property
    def active_workspace_id(self) -> str | None:
        return self._snapshot.active_workspace_id

    def list_workspaces(self) -> list[WorkspaceRef]:
        return list(self._snapshot.workspaces)

    def get(self, workspace_id: str) -> WorkspaceRef:
        for workspace in self._snapshot.workspaces:
            if workspace.workspace_id == workspace_id:
                return workspace
        raise WorkspaceNotFoundError(workspace_id)

    def active(self) -> WorkspaceRef:
        if not self._snapshot.active_workspace_id:
            raise WorkspaceNotFoundError("no active workspace")
        return self.get(self._snapshot.active_workspace_id)

    def add_workspace(self, workspace: WorkspaceRef, *, activate: bool = False, persist: bool = True) -> WorkspaceRef:
        normalized = workspace.normalized()
        if any(existing.workspace_id == normalized.workspace_id for existing in self._snapshot.workspaces):
            raise DuplicateWorkspaceError(normalized.workspace_id)
        if normalized.is_default:
            self._snapshot.workspaces = [
                WorkspaceRef(
                    workspace_id=item.workspace_id,
                    name=item.name,
                    root_path=item.root_path,
                    is_default=False,
                    created_at=item.created_at,
                    last_opened_at=item.last_opened_at,
                    metadata=dict(item.metadata),
                )
                for item in self._snapshot.workspaces
            ]
        self._snapshot.workspaces.append(normalized)
        if activate or self._snapshot.active_workspace_id is None:
            self._snapshot.active_workspace_id = normalized.workspace_id
        if persist:
            self.save()
        return normalized

    def switch(self, workspace_id: str) -> WorkspaceRef:
        workspace = self.get(workspace_id).mark_opened()
        self._replace(workspace)
        self._snapshot.active_workspace_id = workspace.workspace_id
        self.save()
        return workspace

    def remove(self, workspace_id: str) -> None:
        workspace = self.get(workspace_id)
        if workspace.is_default:
            raise ValueError("default workspace cannot be removed")
        self._snapshot.workspaces = [item for item in self._snapshot.workspaces if item.workspace_id != workspace_id]
        if self._snapshot.active_workspace_id == workspace_id:
            default = self.default_workspace()
            self._snapshot.active_workspace_id = default.workspace_id
        self.save()

    def default_workspace(self) -> WorkspaceRef:
        for workspace in self._snapshot.workspaces:
            if workspace.is_default:
                return workspace
        if self._snapshot.workspaces:
            first = self._snapshot.workspaces[0]
            default = WorkspaceRef(
                workspace_id=first.workspace_id,
                name=first.name,
                root_path=first.root_path,
                is_default=True,
                created_at=first.created_at,
                last_opened_at=first.last_opened_at,
                metadata=dict(first.metadata),
            )
            self._replace(default)
            self.save()
            return default
        raise WorkspaceNotFoundError("default")

    def snapshot(self) -> WorkspaceRegistrySnapshot:
        return WorkspaceRegistrySnapshot(
            active_workspace_id=self._snapshot.active_workspace_id,
            workspaces=self.list_workspaces(),
        )

    def save(self) -> None:
        self.store.save(self._snapshot)

    def _replace(self, workspace: WorkspaceRef) -> None:
        self._snapshot.workspaces = [
            workspace if item.workspace_id == workspace.workspace_id else item
            for item in self._snapshot.workspaces
        ]
