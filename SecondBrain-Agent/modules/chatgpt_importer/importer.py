"""ChatGPT adapter for the central v30.51 streaming import engine."""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from secondbrain.importing import StreamingImportService

DEFAULT_AGENT_ROOT = Path(r"H:\SecondBrainAgent\SecondBrain-Agent")
DEFAULT_TARGET = Path(r"H:\SecondBrainAgent\SecondBrain\05_Quellen\ChatGPT")
DEFAULT_PROCESSED = Path(r"H:\SecondBrainAgent\SecondBrain-Inbox\ChatGPT\processed")
DEFAULT_REPORT = Path(r"H:\SecondBrainAgent\SecondBrain\99_System\chatgpt_import")

TAG_RULES = {
    "tischtennis": ["tischtennis", "ttr", "belag", "holz", "victas", "ventus", "rozena"],
    "sap": ["sap", "p01", "p02", "pfs", "crm", "ctam", "cisco", "ea"],
    "obsidian": ["obsidian", "vault", "secondbrain", "markdown", "mcp"],
    "ki": ["chatgpt", "claude", "gemini", "perplexity", "ollama", "ki", "ai"],
    "gesundheit": ["diabetes", "gewicht", "hba1c", "ozempic", "tresiba", "training"],
    "projekt": ["projekt", "roadmap", "sprint", "release", "backlog"],
    "code": ["python", "docker", "github", "react", "typescript", "postgres"],
    "verein": ["ttc", "zaberfeld", "verein", "turnier", "jedermann"],
}

OPENAI_API_KEY_PATTERN = re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}")
REDACTED_OPENAI_API_KEY = "[REDACTED_OPENAI_API_KEY]"


def redact_secrets(value: str) -> str:
    return OPENAI_API_KEY_PATTERN.sub(REDACTED_OPENAI_API_KEY, value)


def slugify(value: str, max_len: int = 90) -> str:
    value = re.sub(r"[^\w\sÄÖÜäöüß.-]", "-", value.strip() or "Ohne Titel", flags=re.UNICODE)
    return re.sub(r"-+", "-", re.sub(r"\s+", "_", value))[:max_len].strip("._-") or "Ohne_Titel"


def message_text(message: dict[str, Any]) -> str:
    parts = (message.get("content") or {}).get("parts") or []
    if not isinstance(parts, list):
        return str(parts).strip()
    return "\n".join(part if isinstance(part, str) else json.dumps(part, ensure_ascii=False, default=str) for part in parts).strip()


def extract_messages(conversation: dict[str, Any]) -> list[dict[str, str]]:
    rows = []
    for node in (conversation.get("mapping") or {}).values():
        message = node.get("message") if isinstance(node, dict) else None
        if not message:
            continue
        text = message_text(message)
        if text:
            rows.append({"role": ((message.get("author") or {}).get("role")) or "unknown", "text": text, "time": str(message.get("create_time") or 0)})
    def sort_key(row: dict[str, str]) -> float:
        try: return float(row["time"])
        except ValueError: return 0.0
    return sorted(rows, key=sort_key)


def derive_tags(title: str, body: str) -> list[str]:
    text = f"{title}\n{body}".lower()
    return sorted({"chatgpt", "import", *(tag for tag, words in TAG_RULES.items() if any(word in text for word in words))})


def frontmatter(title: str, created: str, tags: list[str], source_id: str = "") -> str:
    tag_lines = "\n".join(f"  - {tag}" for tag in tags)
    return f'---\ntitle: "{title.replace(chr(34), chr(39))}"\ntype: chatgpt_conversation\nsource: chatgpt\nsource_id: "{source_id}"\ncreated: {created}\ntags:\n{tag_lines}\n---\n\n'


def conversation_to_markdown(conversation: dict[str, Any]) -> tuple[str, str]:
    title = str(conversation.get("title") or "ChatGPT Unterhaltung")
    conversation_id = str(conversation.get("id") or "")
    created = datetime.now().strftime("%Y-%m-%d")
    try:
        if conversation.get("create_time"):
            created = datetime.fromtimestamp(float(conversation["create_time"])).strftime("%Y-%m-%d")
    except (TypeError, ValueError, OSError):
        pass
    messages = extract_messages(conversation)
    body = "\n\n".join(message["text"] for message in messages)
    lines = [frontmatter(title, created, derive_tags(title, body), conversation_id), f"# {title}", "", "## Metadaten", "",
             "- Quelle: ChatGPT Export", f"- Conversation ID: `{conversation_id}`", f"- Nachrichten: {len(messages)}", "", "## Unterhaltung", ""]
    for index, message in enumerate(messages, 1):
        role = {"user": "Benutzer", "assistant": "Assistent"}.get(message["role"], message["role"])
        lines.extend((f"### {index}. {role}", "", redact_secrets(message["text"]), ""))
    return title, "\n".join(lines).strip() + "\n"


def _report(report_folder: Path, zip_path: Path, session: Any, processed_path: Path | None) -> dict[str, Any]:
    report_folder.mkdir(parents=True, exist_ok=True)
    report = {"time": datetime.now().isoformat(timespec="seconds"), "zip": str(zip_path), "session_id": session.session_id,
              "status": session.status, "imported_count": session.imported_chats, "skipped_count": 0,
              "error_count": 1 if session.error else 0, "errors": [session.error] if session.error else [],
              "chunks": session.chunks, "embeddings": session.embeddings, "bytes": session.bytes_processed,
              "processed_copy": str(processed_path) if processed_path else ""}
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    json_path = report_folder / f"{stamp}_chatgpt_import_report.json"
    md_path = report_folder / f"{stamp}_chatgpt_import_report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(f"# ChatGPT Streaming Import\n\nSession: `{session.session_id}`\n\nImportiert: {session.imported_chats}\n\nChunks: {session.chunks}\n\nStatus: {session.status}\n", encoding="utf-8")
    return {**report, "imported": [], "skipped": [], "report_json": str(json_path), "report_md": str(md_path)}


def import_chatgpt_zip(zip_path: str | Path, target_folder: str | Path = DEFAULT_TARGET,
                       processed_folder: str | Path = DEFAULT_PROCESSED, report_folder: str | Path = DEFAULT_REPORT,
                       agent_root: str | Path = DEFAULT_AGENT_ROOT, update_semantic_search: bool = True,
                       update_secondbrain_os: bool = False) -> dict[str, Any]:
    del target_folder, update_semantic_search, update_secondbrain_os
    source = Path(zip_path).expanduser().resolve()
    session = StreamingImportService(agent_root).import_file(source, source="chatgpt")
    processed_dir = Path(processed_folder); processed_dir.mkdir(parents=True, exist_ok=True)
    processed = processed_dir / source.name
    if processed.exists():
        processed = processed_dir / f"{source.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{source.suffix}"
    shutil.copy2(source, processed)
    return _report(Path(report_folder), source, session, processed)


def import_exports_folder(exports_folder: str | Path, **kwargs: Any) -> list[dict[str, Any]]:
    folder = Path(exports_folder); folder.mkdir(parents=True, exist_ok=True)
    return [import_chatgpt_zip(path, **kwargs) for path in sorted(folder.glob("*.zip"))]
