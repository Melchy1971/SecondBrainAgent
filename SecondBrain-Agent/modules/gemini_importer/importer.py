"""Gemini adapter for the central v30.51 streaming import engine."""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from secondbrain.importing import StreamingImportService

DEFAULT_AGENT_ROOT = Path(r"H:\SecondBrainAgent\SecondBrain-Agent")
DEFAULT_TARGET = Path(r"H:\SecondBrainAgent\SecondBrain\05_Quellen\Gemini")
DEFAULT_PROCESSED = Path(r"H:\SecondBrainAgent\SecondBrain-Inbox\Gemini\processed")
DEFAULT_REPORT = Path(r"H:\SecondBrainAgent\SecondBrain\99_System\gemini_import")


def import_gemini_export(zip_path: str | Path, target_folder: str | Path = DEFAULT_TARGET,
                         processed_folder: str | Path = DEFAULT_PROCESSED, report_folder: str | Path = DEFAULT_REPORT,
                         agent_root: str | Path = DEFAULT_AGENT_ROOT, update_semantic_search: bool = True) -> dict[str, Any]:
    del target_folder, update_semantic_search
    source = Path(zip_path).expanduser().resolve()
    session = StreamingImportService(agent_root).import_file(source, source="gemini")
    processed_dir = Path(processed_folder); processed_dir.mkdir(parents=True, exist_ok=True)
    processed = processed_dir / source.name
    if processed.exists(): processed = processed_dir / f"{source.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{source.suffix}"
    shutil.copy2(source, processed)
    report_dir = Path(report_folder); report_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    payload = {"time": datetime.now().isoformat(timespec="seconds"), "source": "gemini", "zip": str(source),
               "session_id": session.session_id, "status": session.status, "imported_count": session.imported_chats,
               "error_count": 1 if session.error else 0, "errors": [session.error] if session.error else [],
               "chunks": session.chunks, "embeddings": session.embeddings, "bytes": session.bytes_processed}
    json_path, md_path = report_dir / f"{stamp}_gemini_import_report.json", report_dir / f"{stamp}_gemini_import_report.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(f"# Gemini Streaming Import\n\nSession: `{session.session_id}`\n\nImportiert: {session.imported_chats}\n\nStatus: {session.status}\n", encoding="utf-8")
    return {**payload, "imported": [], "report_json": str(json_path), "report_md": str(md_path)}


def import_gemini_folder(exports_folder: str | Path, **kwargs: Any) -> list[dict[str, Any]]:
    folder = Path(exports_folder); folder.mkdir(parents=True, exist_ok=True)
    return [import_gemini_export(path, **kwargs) for path in sorted(folder.glob("*.zip"))]
