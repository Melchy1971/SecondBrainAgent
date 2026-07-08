"""LibreChat adapter for the Enterprise Streaming Import Engine."""
from pathlib import Path
from typing import Any

from secondbrain.importing import StreamingImportService


def import_librechat_export(path: str | Path, *, agent_root: str | Path = ".", batch_size: int = 500) -> dict[str, Any]:
    session = StreamingImportService(agent_root, batch_size=batch_size).import_file(path, source="librechat")
    return {"ok": session.status == "completed", **session.to_dict()}
