from __future__ import annotations

import json
from pathlib import Path

from .workspace_state import WorkspaceRegistrySnapshot


class WorkspaceStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> WorkspaceRegistrySnapshot:
        if not self.path.exists():
            return WorkspaceRegistrySnapshot(active_workspace_id=None, workspaces=[])
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return WorkspaceRegistrySnapshot.from_dict(data)

    def save(self, snapshot: WorkspaceRegistrySnapshot) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
