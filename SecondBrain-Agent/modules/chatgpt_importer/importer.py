from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile
from datetime import datetime
import json
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any

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
    """Remove API credentials that may occur in imported conversations."""
    return OPENAI_API_KEY_PATTERN.sub(REDACTED_OPENAI_API_KEY, value)

def slugify(value: str, max_len: int = 90) -> str:
    value = value.strip() or "Ohne Titel"
    value = re.sub(r"[^\w\sÄÖÜäöüß.-]", "-", value, flags=re.UNICODE)
    value = re.sub(r"\s+", "_", value)
    value = re.sub(r"-+", "-", value)
    return value[:max_len].strip("._-") or "Ohne_Titel"

def safe_read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))

def find_conversations_json(extracted: Path) -> list[Path]:
    """Findet die Konversationsdatei(en) im Export.

    Unterstuetzt das alte Einzelformat (conversations.json) und das aktuelle
    OpenAI-Splitformat (conversations-000.json ... conversations-NNN.json).
    Gibt eine sortierte Liste zurueck.
    """
    single = list(extracted.rglob("conversations.json"))
    if single:
        return sorted(single)

    def split_key(p: Path):
        match = re.search(r"conversations-(\d+)\.json$", p.name)
        return int(match.group(1)) if match else 0

    split = sorted(extracted.rglob("conversations-*.json"), key=split_key)
    if split:
        return split

    raise FileNotFoundError(
        "Weder conversations.json noch conversations-*.json gefunden."
    )

def message_text(message: dict[str, Any]) -> str:
    content = message.get("content") or {}
    parts = content.get("parts") or []
    if isinstance(parts, list):
        out = []
        for part in parts:
            if isinstance(part, str):
                out.append(part)
            elif isinstance(part, dict):
                out.append(json.dumps(part, ensure_ascii=False))
            else:
                out.append(str(part))
        return "\n".join(out).strip()
    return str(parts).strip()

def extract_messages(conversation: dict[str, Any]) -> list[dict[str, str]]:
    mapping = conversation.get("mapping") or {}
    nodes = []

    for node_id, node in mapping.items():
        msg = node.get("message")
        if not msg:
            continue
        author = ((msg.get("author") or {}).get("role")) or "unknown"
        text = message_text(msg)
        if not text:
            continue
        create_time = msg.get("create_time") or 0
        nodes.append({
            "role": author,
            "text": text,
            "time": str(create_time),
        })

    # ChatGPT export mapping is mostly chronological by create_time
    def sort_key(x):
        try:
            return float(x["time"])
        except Exception:
            return 0

    return sorted(nodes, key=sort_key)

def derive_tags(title: str, body: str) -> list[str]:
    low = (title + "\n" + body).lower()
    tags = ["chatgpt", "import"]
    for tag, keys in TAG_RULES.items():
        if any(k.lower() in low for k in keys):
            tags.append(tag)
    return sorted(set(tags))

def frontmatter(title: str, created: str, tags: list[str], source_id: str = "") -> str:
    tag_lines = "\n".join(f"  - {tag}" for tag in tags)
    return f"""---
title: "{title.replace('"', "'")}"
type: chatgpt_conversation
source: chatgpt
source_id: "{source_id}"
created: {created}
tags:
{tag_lines}
---

"""

def conversation_to_markdown(conversation: dict[str, Any]) -> tuple[str, str]:
    title = conversation.get("title") or "ChatGPT Unterhaltung"
    conv_id = conversation.get("id") or ""
    created = datetime.now().strftime("%Y-%m-%d")
    if conversation.get("create_time"):
        try:
            created = datetime.fromtimestamp(float(conversation["create_time"])).strftime("%Y-%m-%d")
        except Exception:
            pass

    messages = extract_messages(conversation)
    raw_body = "\n\n".join(m["text"] for m in messages)
    tags = derive_tags(title, raw_body)

    lines = [
        frontmatter(title, created, tags, conv_id),
        f"# {title}",
        "",
        "## Metadaten",
        "",
        f"- Quelle: ChatGPT Export",
        f"- Conversation ID: `{conv_id}`",
        f"- Nachrichten: {len(messages)}",
        "",
        "## Kurzüberblick",
        "",
        "Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.",
        "",
        "## Unterhaltung",
        "",
    ]

    for i, msg in enumerate(messages, start=1):
        role = msg["role"]
        heading = "Benutzer" if role == "user" else "Assistent" if role == "assistant" else role
        lines.append(f"### {i}. {heading}")
        lines.append("")
        lines.append(redact_secrets(msg["text"]))
        lines.append("")

    return title, "\n".join(lines).strip() + "\n"

def import_chatgpt_zip(
    zip_path: str | Path,
    target_folder: str | Path = DEFAULT_TARGET,
    processed_folder: str | Path = DEFAULT_PROCESSED,
    report_folder: str | Path = DEFAULT_REPORT,
    agent_root: str | Path = DEFAULT_AGENT_ROOT,
    update_semantic_search: bool = True,
    update_secondbrain_os: bool = False,
) -> dict[str, Any]:
    zip_path = Path(zip_path)
    target_folder = Path(target_folder)
    processed_folder = Path(processed_folder)
    report_folder = Path(report_folder)
    agent_root = Path(agent_root)

    target_folder.mkdir(parents=True, exist_ok=True)
    processed_folder.mkdir(parents=True, exist_ok=True)
    report_folder.mkdir(parents=True, exist_ok=True)

    if not zip_path.exists():
        raise FileNotFoundError(str(zip_path))

    imported = []
    skipped = []
    errors = []

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        with ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_path)

        conversation_files = find_conversations_json(tmp_path)
        conversations: list[Any] = []
        for conv_file in conversation_files:
            part = safe_read_json(conv_file)
            if not isinstance(part, list):
                raise ValueError(
                    f"{conv_file.name} hat kein erwartetes Listenformat."
                )
            conversations.extend(part)

        for index, conv in enumerate(conversations, start=1):
            try:
                title, md = conversation_to_markdown(conv)
                filename = slugify(title)
                target = target_folder / f"{filename}.md"

                if target.exists():
                    suffix = conv.get("id") or str(index)
                    target = target_folder / f"{filename}_{slugify(str(suffix), 24)}.md"

                target.write_text(md, encoding="utf-8")
                imported.append(str(target))
            except Exception as exc:
                errors.append({"index": index, "error": str(exc)})

    # Move original ZIP to processed
    processed_target = processed_folder / zip_path.name
    if zip_path.exists():
        try:
            if processed_target.exists():
                processed_target = processed_folder / f"{zip_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{zip_path.suffix}"
            shutil.copy2(zip_path, processed_target)
        except Exception as exc:
            errors.append({"move_processed": str(exc)})

    semantic_result = ""
    if update_semantic_search:
        script = agent_root / "scripts" / "semantic_search.py"
        if script.exists():
            try:
                result = subprocess.run(
                    [sys.executable, str(script), "ChatGPT Import"],
                    cwd=str(agent_root),
                    capture_output=True,
                    text=True,
                    timeout=180,
                )
                semantic_result = (result.stdout + "\n" + result.stderr)[-2000:]
            except Exception as exc:
                semantic_result = f"Semantic Search Update fehlgeschlagen: {exc}"

    os_result = ""
    if update_secondbrain_os:
        script = agent_root / "scripts" / "run_secondbrain_os_cycle.py"
        if script.exists():
            try:
                result = subprocess.run(
                    [sys.executable, str(script)],
                    cwd=str(agent_root),
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                os_result = (result.stdout + "\n" + result.stderr)[-2000:]
            except Exception as exc:
                os_result = f"OS Cycle fehlgeschlagen: {exc}"

    report = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "zip": str(zip_path),
        "imported_count": len(imported),
        "skipped_count": len(skipped),
        "error_count": len(errors),
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
        "semantic_result": semantic_result,
        "os_result": os_result,
    }

    report_path = report_folder / f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}_chatgpt_import_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md_report = report_folder / f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}_chatgpt_import_report.md"
    lines = [
        "# ChatGPT Import Report",
        "",
        f"Zeit: {report['time']}",
        f"ZIP: `{zip_path}`",
        f"Importiert: {len(imported)}",
        f"Fehler: {len(errors)}",
        "",
        "## Importierte Dateien",
        "",
    ]
    lines += [f"- `{p}`" for p in imported[:200]] or ["- Keine."]
    if errors:
        lines += ["", "## Fehler", ""]
        lines += [f"- {e}" for e in errors]
    md_report.write_text("\n".join(lines), encoding="utf-8")

    report["report_json"] = str(report_path)
    report["report_md"] = str(md_report)
    return report

def import_exports_folder(exports_folder: str | Path, **kwargs) -> list[dict[str, Any]]:
    exports_folder = Path(exports_folder)
    exports_folder.mkdir(parents=True, exist_ok=True)
    reports = []
    for zip_file in sorted(exports_folder.glob("*.zip")):
        reports.append(import_chatgpt_zip(zip_file, **kwargs))
    return reports
