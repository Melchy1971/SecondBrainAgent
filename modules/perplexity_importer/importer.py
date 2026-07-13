"""Perplexity adapter for the Enterprise Streaming Import Engine."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from secondbrain.importing import StreamingImportService

DEFAULT_AGENT_ROOT = Path(r"H:\SecondBrainAgent\SecondBrain-Agent")


def import_perplexity_export(path: str | Path, target_folder: str | Path | None = None,
                             processed_folder: str | Path | None = None, report_folder: str | Path | None = None,
                             agent_root: str | Path = DEFAULT_AGENT_ROOT,
                             update_semantic_search: bool = True, batch_size: int = 500) -> dict[str, Any]:
    del target_folder, processed_folder, report_folder, update_semantic_search
    session = StreamingImportService(agent_root, batch_size=batch_size).import_file(path, source="perplexity")
    return {"ok": session.status == "completed", **session.to_dict()}


def import_perplexity_folder(exports_folder: str | Path, **kwargs: Any) -> list[dict[str, Any]]:
    folder = Path(exports_folder)
    suffixes = {".zip", ".json", ".jsonl", ".ndjson", ".md", ".markdown", ".txt", ".html"}
    return [import_perplexity_export(path, **kwargs) for path in sorted(folder.iterdir()) if path.is_file() and path.suffix.lower() in suffixes]
