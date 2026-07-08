"""v30.46.1 - ConversationExporter/-Importer.

Export delegiert an ConversationStore.export (json/md, unveraendertes
Schema). Import liest die eigenen Exporte zurueck: JSON-Roundtrip
({"conversation": {...}, "messages": [...]}) sowie das md-Exportformat
(## Role-Abschnitte).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from secondbrain.native.chat import ConversationStore


class ConversationExporter:
    def __init__(self, store: ConversationStore) -> None:
        self.store = store

    def export(self, conversation_id: str, *, format: str = "json") -> dict[str, Any]:
        return self.store.export(conversation_id, format=format)


class ConversationImporter:
    SUPPORTED = {".json", ".md"}

    def __init__(self, store: ConversationStore) -> None:
        self.store = store

    def import_file(self, path: str | Path) -> dict[str, Any]:
        source = Path(path).expanduser()
        if not source.is_file():
            return {"ok": False, "status": "source_not_found", "path": str(source)}
        suffix = source.suffix.lower()
        if suffix not in self.SUPPORTED:
            return {"ok": False, "status": "unsupported_format", "format": suffix}
        try:
            if suffix == ".json":
                title, meta, messages = self._parse_json(source)
            else:
                title, meta, messages = self._parse_md(source)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            return {"ok": False, "status": "parse_error", "error": f"{type(exc).__name__}: {exc}", "path": str(source)}
        if not messages:
            return {"ok": False, "status": "no_messages", "path": str(source)}
        conversation = self.store.create(
            f"{title} (Import)",
            workspace=str(meta.get("workspace") or "chat"),
            provider=str(meta.get("provider") or "ollama"),
            model=str(meta.get("model") or "llama3.2"),
        )
        for row in messages:
            role = str(row.get("role") or "user")
            if role not in {"system", "user", "assistant", "tool"}:
                role = "user"
            self.store.append_message(
                conversation["id"],
                role,
                str(row.get("content") or ""),
                metadata={**dict(row.get("metadata") or {}), "imported_from": str(source)},
            )
        return {
            "ok": True,
            "status": "imported",
            "conversation": self.store.get(conversation["id"]) or conversation,
            "messages": len(messages),
            "path": str(source),
        }

    @staticmethod
    def _parse_json(source: Path) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
        payload = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("json export must be an object")
        conversation = payload.get("conversation") or {}
        messages = payload.get("messages")
        if not isinstance(messages, list):
            raise ValueError("json export requires a messages list")
        title = str(conversation.get("title") or source.stem)
        return title, dict(conversation), [row for row in messages if isinstance(row, dict)]

    @staticmethod
    def _parse_md(source: Path) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
        title = source.stem
        messages: list[dict[str, Any]] = []
        role: str | None = None
        body: list[str] = []

        def flush() -> None:
            if role is not None:
                content = "\n".join(body).strip()
                if content:
                    messages.append({"role": role.lower(), "content": content})

        for line in source.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("# ") and not messages and role is None:
                title = line[2:].strip() or title
            elif line.startswith("## "):
                flush()
                role = line[3:].strip()
                body = []
            elif role is not None:
                body.append(line)
        flush()
        return title, {}, messages
