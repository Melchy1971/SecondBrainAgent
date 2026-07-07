"""ChatGPT adapter for the Enterprise Streaming Import Engine."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from secondbrain.importing import StreamingImportService
from secondbrain.importing.normalization import redact

DEFAULT_AGENT_ROOT = Path(r"H:\SecondBrainAgent\SecondBrain-Agent")
DEFAULT_TARGET = Path(r"H:\SecondBrainAgent\SecondBrain\05_Quellen\ChatGPT")
DEFAULT_PROCESSED = Path(r"H:\SecondBrainAgent\SecondBrain-Inbox\ChatGPT\processed")
DEFAULT_REPORT = Path(r"H:\SecondBrainAgent\SecondBrain\99_System\chatgpt_import")
REDACTED_OPENAI_API_KEY = "[REDACTED_OPENAI_API_KEY]"


def redact_secrets(value: str) -> str:
    return redact(value)


def conversation_to_markdown(conversation: dict[str, Any]) -> tuple[str, str]:
    normalized = StreamingImportService.normalize(conversation, "chatgpt", "conversations.json")
    return normalized.title, normalized.render()


def import_chatgpt_zip(zip_path: str | Path, target_folder: str | Path = DEFAULT_TARGET,
                       processed_folder: str | Path = DEFAULT_PROCESSED, report_folder: str | Path = DEFAULT_REPORT,
                       agent_root: str | Path = DEFAULT_AGENT_ROOT, update_semantic_search: bool = True,
                       update_secondbrain_os: bool = False, batch_size: int = 500) -> dict[str, Any]:
    del target_folder, processed_folder, report_folder, update_semantic_search, update_secondbrain_os
    session = StreamingImportService(agent_root, batch_size=batch_size).import_file(zip_path, source="chatgpt")
    return {"ok": session.status == "completed", **session.to_dict()}


def import_exports_folder(exports_folder: str | Path, **kwargs: Any) -> list[dict[str, Any]]:
    folder = Path(exports_folder)
    return [import_chatgpt_zip(path, **kwargs) for path in sorted(folder.glob("*.zip"))]
