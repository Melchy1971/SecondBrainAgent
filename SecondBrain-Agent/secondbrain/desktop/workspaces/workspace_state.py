from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class WorkspaceRef:
    workspace_id: str
    name: str
    root_path: str
    is_default: bool = False
    created_at: str = field(default_factory=utc_now_iso)
    last_opened_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def id(self) -> str:
        """Backward-compatible desktop workspace identifier alias."""
        return self.workspace_id

    def normalized(self) -> "WorkspaceRef":
        workspace_id = self.workspace_id.strip()
        name = self.name.strip()
        root = str(Path(self.root_path).expanduser())
        if not workspace_id:
            raise ValueError("workspace_id must not be empty")
        if not name:
            raise ValueError("workspace name must not be empty")
        if not root:
            raise ValueError("workspace root_path must not be empty")
        return WorkspaceRef(
            workspace_id=workspace_id,
            name=name,
            root_path=root,
            is_default=self.is_default,
            created_at=self.created_at or utc_now_iso(),
            last_opened_at=self.last_opened_at,
            metadata=dict(self.metadata or {}),
        )

    def mark_opened(self) -> "WorkspaceRef":
        return WorkspaceRef(
            workspace_id=self.workspace_id,
            name=self.name,
            root_path=self.root_path,
            is_default=self.is_default,
            created_at=self.created_at,
            last_opened_at=utc_now_iso(),
            metadata=dict(self.metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "WorkspaceRef":
        return WorkspaceRef(
            workspace_id=str(data.get("workspace_id", "")),
            name=str(data.get("name", "")),
            root_path=str(data.get("root_path", "")),
            is_default=bool(data.get("is_default", False)),
            created_at=str(data.get("created_at") or utc_now_iso()),
            last_opened_at=data.get("last_opened_at"),
            metadata=dict(data.get("metadata") or {}),
        ).normalized()


@dataclass
class WorkspaceRegistrySnapshot:
    active_workspace_id: str | None
    workspaces: list[WorkspaceRef]

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_workspace_id": self.active_workspace_id,
            "workspaces": [workspace.to_dict() for workspace in self.workspaces],
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "WorkspaceRegistrySnapshot":
        return WorkspaceRegistrySnapshot(
            active_workspace_id=data.get("active_workspace_id"),
            workspaces=[WorkspaceRef.from_dict(item) for item in data.get("workspaces", [])],
        )
