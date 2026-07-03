"""Claude adapter for the central v30.51 streaming import engine."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from secondbrain.importing import StreamingImportService


def import_claude_export(path: str | Path, *, agent_root: str | Path = ".", batch_size: int = 500) -> dict[str, Any]:
    session = StreamingImportService(agent_root, batch_size=batch_size).import_file(path, source="claude")
    return {"ok": session.status == "completed", **session.to_dict()}
