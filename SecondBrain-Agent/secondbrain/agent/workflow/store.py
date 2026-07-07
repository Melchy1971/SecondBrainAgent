"""v30.62 Agent Workflow Engine - checkpoint persistence.

One JSON file per workflow under ``runtime/agent/workflows/<id>.json``. Writing
is atomic (temp file + replace) so a crash mid-write cannot corrupt the
checkpoint that crash-recovery depends on.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .models import WorkflowCheckpoint


def workflows_dir(root: str | Path) -> Path:
    return Path(root).resolve() / "runtime" / "agent" / "workflows"


class WorkflowStore:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()
        self.dir = workflows_dir(self.project_root)

    def _path(self, workflow_id: str) -> Path:
        return self.dir / f"{workflow_id}.json"

    def save(self, checkpoint: WorkflowCheckpoint) -> WorkflowCheckpoint:
        self.dir.mkdir(parents=True, exist_ok=True)
        path = self._path(checkpoint.workflow_id)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(checkpoint.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, path)
        return checkpoint

    def load(self, workflow_id: str) -> WorkflowCheckpoint | None:
        path = self._path(workflow_id)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        return WorkflowCheckpoint.from_dict(data)

    def exists(self, workflow_id: str) -> bool:
        return self._path(workflow_id).exists()

    def list_ids(self) -> list[str]:
        if not self.dir.exists():
            return []
        return sorted(p.stem for p in self.dir.glob("*.json"))

    def list(self) -> list[WorkflowCheckpoint]:
        result: list[WorkflowCheckpoint] = []
        for wid in self.list_ids():
            cp = self.load(wid)
            if cp is not None:
                result.append(cp)
        return result

    def delete(self, workflow_id: str) -> bool:
        path = self._path(workflow_id)
        if path.exists():
            path.unlink()
            return True
        return False
