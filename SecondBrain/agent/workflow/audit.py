"""v30.62 Agent Workflow Engine - WorkflowAudit.

Append-only JSONL trail of every workflow lifecycle event. This is the durable
event memory of a run: it is what crash-recovery and post-mortem inspection read
back, and what an external memory sink can be fed from.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

AUDIT_SCHEMA = "secondbrain.agent.workflow.audit.v30_62"


def audit_path(root: str | Path) -> Path:
    return Path(root).resolve() / "runtime" / "agent" / "workflows" / "workflow_audit.jsonl"


class WorkflowAudit:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()
        self.path = audit_path(self.project_root)

    def record(
        self,
        *,
        workflow_id: str,
        event: str,
        state: str = "",
        step_id: str = "",
        detail: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "schema": AUDIT_SCHEMA,
            "id": uuid4().hex[:16],
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "workflow_id": workflow_id,
            "event": event,
            "state": state,
            "step_id": step_id,
            "detail": detail or {},
        }
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def events(self, workflow_id: str | None = None, *, limit: int = 200) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if workflow_id is None or row.get("workflow_id") == workflow_id:
                rows.append(row)
        return rows[-max(1, int(limit)):]
