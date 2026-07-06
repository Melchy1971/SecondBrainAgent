"""Gemini adapter for the Enterprise Streaming Import Engine."""
from pathlib import Path
from typing import Any

from secondbrain.importing import StreamingImportService

DEFAULT_AGENT_ROOT = Path(r"H:\SecondBrainAgent\SecondBrain-Agent")
DEFAULT_TARGET = Path(r"H:\SecondBrainAgent\SecondBrain\05_Quellen\Gemini")
DEFAULT_PROCESSED = Path(r"H:\SecondBrainAgent\SecondBrain-Inbox\Gemini\processed")
DEFAULT_REPORT = Path(r"H:\SecondBrainAgent\SecondBrain\99_System\gemini_import")


def import_gemini_export(path: str | Path, target_folder: str | Path = DEFAULT_TARGET,
                         processed_folder: str | Path = DEFAULT_PROCESSED, report_folder: str | Path = DEFAULT_REPORT,
                         agent_root: str | Path = DEFAULT_AGENT_ROOT, update_semantic_search: bool = True,
                         batch_size: int = 500) -> dict[str, Any]:
    del target_folder, processed_folder, report_folder, update_semantic_search
    session = StreamingImportService(agent_root, batch_size=batch_size).import_file(path, source="gemini")
    return {"ok": session.status == "completed", **session.to_dict()}


def import_gemini_folder(exports_folder: str | Path, **kwargs: Any) -> list[dict[str, Any]]:
    folder = Path(exports_folder)
    return [import_gemini_export(path, **kwargs) for path in sorted(folder.glob("*.zip"))]
