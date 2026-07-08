"""Canonical conversation model and provider normalizers."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

OPENAI_KEY = re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}")


def redact(value: str) -> str:
    return OPENAI_KEY.sub("[REDACTED_OPENAI_API_KEY]", value)


@dataclass(frozen=True, slots=True)
class Source:
    provider: str
    file: str
    export_id: str = ""


@dataclass(frozen=True, slots=True)
class Metadata:
    values: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Attachment:
    id: str
    name: str
    kind: str = "file"
    uri: str = ""
    mime_type: str = ""
    metadata: Metadata = field(default_factory=Metadata)


@dataclass(frozen=True, slots=True)
class Message:
    id: str
    role: str
    content: str
    created_at: str = ""
    attachments: tuple[Attachment, ...] = ()
    metadata: Metadata = field(default_factory=Metadata)


@dataclass(frozen=True, slots=True)
class Conversation:
    id: str
    title: str
    messages: tuple[Message, ...]
    attachments: tuple[Attachment, ...]
    source: Source
    metadata: Metadata = field(default_factory=Metadata)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def render(self) -> str:
        lines = [f"# {self.title}", "", f"Source: {self.source.provider}", f"Conversation: {self.id}", ""]
        for message in self.messages:
            lines.extend((f"## {message.role}", "", redact(message.content), ""))
            for attachment in message.attachments:
                lines.append(f"- Attachment: {attachment.name} ({attachment.uri or attachment.name})")
            if message.attachments:
                lines.append("")
        return "\n".join(lines).strip() + "\n"


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(filter(None, (_text(item) for item in value)))
    if isinstance(value, dict):
        if "parts" in value:
            return _text(value["parts"])
        for key in ("text", "content", "value", "message"):
            if key in value:
                return _text(value[key])
    return json.dumps(value, ensure_ascii=False, default=str)


def _attachment(value: Any, index: int) -> Attachment | None:
    if isinstance(value, str):
        return Attachment(f"att_{index}", Path(value).name or value, uri=value)
    if not isinstance(value, dict):
        return None
    uri = str(value.get("url") or value.get("uri") or value.get("path") or value.get("download_url") or "")
    name = str(value.get("name") or value.get("filename") or value.get("title") or Path(uri).name or f"attachment-{index}")
    identifier = str(value.get("id") or value.get("file_id") or f"att_{index}")
    return Attachment(identifier, name, str(value.get("kind") or value.get("type") or "file"), uri,
                      str(value.get("mime_type") or value.get("mime") or ""))


def _attachments(row: dict[str, Any]) -> tuple[Attachment, ...]:
    raw = row.get("attachments") or row.get("files") or row.get("file_ids") or []
    raw = list(raw.values()) if isinstance(raw, dict) else raw
    raw = raw if isinstance(raw, list) else [raw]
    return tuple(item for index, value in enumerate(raw, 1) if (item := _attachment(value, index)) is not None)


def _message(row: Any, index: int) -> Message | None:
    if not isinstance(row, dict):
        content = _text(row)
        return Message(f"msg_{index}", "unknown", content) if content else None
    author = row.get("author")
    if isinstance(author, dict):
        author = author.get("role") or author.get("name")
    role = str(row.get("role") or row.get("sender") or row.get("from") or author or "unknown")
    content = _text(row.get("content") if "content" in row else row.get("text") or row.get("message") or row.get("response") or row.get("answer") or row.get("prompt"))
    attachments = _attachments(row)
    if not content and not attachments:
        return None
    known = {"id", "uuid", "message_id", "role", "sender", "from", "author", "content", "text", "message", "response", "created_at", "create_time", "timestamp", "time", "attachments", "files", "file_ids"}
    metadata = {key: value for key, value in row.items() if key not in known and not isinstance(value, (dict, list))}
    return Message(str(row.get("id") or row.get("uuid") or row.get("message_id") or f"msg_{index}"), role, redact(content),
                   str(row.get("created_at") or row.get("create_time") or row.get("timestamp") or row.get("time") or ""),
                   attachments, Metadata(metadata))


def _chatgpt_messages(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [node.get("message") for node in (data.get("mapping") or {}).values() if isinstance(node, dict) and node.get("message")]
    def order(row: dict[str, Any]) -> float:
        try:
            return float(row.get("create_time") or 0)
        except (TypeError, ValueError):
            return 0.0
    return sorted(rows, key=order)


def normalize_conversation(raw: Any, provider: str, path: Path, position: int) -> Conversation:
    provider = provider.strip().lower().replace(" ", "_") or "file"
    if isinstance(raw, dict) and set(raw) == {"name", "value"} and isinstance(raw.get("value"), (dict, list)):
        raw = raw["value"]
    if isinstance(raw, dict) and provider == "openwebui" and isinstance(raw.get("chat"), dict):
        raw = {**raw, **raw["chat"]}
    data = raw if isinstance(raw, dict) else {"content": raw}
    conversation_id = str(data.get("id") or data.get("uuid") or data.get("conversation_id") or data.get("conversationId") or data.get("thread_id") or position)
    title = str(data.get("title") or data.get("name") or data.get("query") or f"{provider.title()} Import {position}")
    if provider in {"chatgpt", "openai", "openai_export"} and data.get("mapping"):
        raw_messages: Any = _chatgpt_messages(data)
    else:
        raw_messages = data.get("messages") or data.get("chat_messages") or data.get("history") or data.get("conversation") or data.get("chats") or []
    if isinstance(raw_messages, dict) and isinstance(raw_messages.get("messages"), (list, dict)):
        raw_messages = raw_messages["messages"]
    if provider == "anythingllm" and isinstance(raw_messages, list):
        expanded = []
        for row in raw_messages:
            if isinstance(row, dict) and ("prompt" in row or "response" in row):
                expanded.extend(({"id": f"{row.get('id', '')}-prompt", "role": "user", "content": row.get("prompt")},
                                 {"id": f"{row.get('id', '')}-response", "role": "assistant", "content": row.get("response")}))
            else:
                expanded.append(row)
        raw_messages = expanded
    if isinstance(raw_messages, dict):
        raw_messages = list(raw_messages.values())
    if not isinstance(raw_messages, list):
        raw_messages = [raw_messages]
    if provider == "perplexity" and not raw_messages:
        raw_messages = [{"role": "user", "content": data.get("query") or data.get("question")},
                        {"role": "assistant", "content": data.get("answer") or data.get("response") or data.get("content"),
                         "attachments": data.get("sources") or data.get("citations")}]
    if provider == "gemini" and not raw_messages:
        raw_messages = [{"role": "user", "content": data.get("prompt") or data.get("chunkedPrompt") or data.get("user_query") or data.get("question")},
                        {"role": "assistant", "content": data.get("response") or data.get("chunkedResponse") or data.get("answer") or data.get("content")}]
    if not raw_messages:
        raw_messages = [{"role": data.get("role") or "document", "content": data.get("content") or data.get("text") or data}]
    messages = tuple(message for index, row in enumerate(raw_messages, 1) if (message := _message(row, index)) is not None)
    all_attachments = {item.id: item for item in _attachments(data)}
    for message in messages:
        all_attachments.update({item.id: item for item in message.attachments})
    known = {"id", "uuid", "conversation_id", "conversationId", "thread_id", "title", "name", "query", "question", "messages", "chat_messages", "history", "conversation", "chats", "mapping", "attachments", "files", "file_ids", "content", "text", "response", "answer", "prompt", "chunkedPrompt", "chunkedResponse", "user_query", "chat"}
    metadata = {key: value for key, value in data.items() if key not in known and not isinstance(value, (dict, list))}
    export_id = str(data.get("export_id") or data.get("source_id") or conversation_id)
    return Conversation(conversation_id, title, messages, tuple(all_attachments.values()), Source(provider, str(path), export_id), Metadata(metadata))


def document_record(conversation: Conversation, path: Path, position: int) -> dict[str, Any]:
    seed = f"{path}|{conversation.id}"
    messages = [{"id": item.id, "role": item.role, "created_at": item.created_at,
                 "attachments": [attachment.id for attachment in item.attachments]} for item in conversation.messages]
    return {"id": f"doc_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:24]}", "title": conversation.title,
            "content": conversation.render(), "position": position,
            "metadata": {"schema": "secondbrain.conversation.v1", "conversation_id": conversation.id,
                         "source": asdict(conversation.source), "metadata": conversation.metadata.values,
                         "messages": messages, "attachments": [asdict(item) for item in conversation.attachments]}}
