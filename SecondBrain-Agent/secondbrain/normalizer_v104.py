from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any
import hashlib
import re


_WS = re.compile(r"\s+")


@dataclass(frozen=True)
class NormalizedRecord:
    """Connector-neutral document unit before writing to memory or graph."""

    source: str
    external_id: str
    title: str
    body: str
    record_type: str
    author: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    url: str | None = None
    metadata: dict[str, Any] | None = None
    content_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if not data["content_hash"]:
            data["content_hash"] = stable_hash(self.title + "\n" + self.body)
        return data


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return _WS.sub(" ", value.replace("\x00", " ")).strip()


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_email(raw: dict[str, Any], source: str = "email") -> NormalizedRecord:
    subject = clean_text(raw.get("subject") or "Ohne Betreff")
    sender = clean_text(raw.get("from") or raw.get("sender") or "")
    body = clean_text(raw.get("body") or raw.get("snippet") or "")
    external_id = str(raw.get("id") or raw.get("message_id") or stable_hash(subject + sender + body))
    return NormalizedRecord(
        source=source,
        external_id=external_id,
        title=subject,
        body=body,
        record_type="email",
        author=sender or None,
        created_at=raw.get("date") or raw.get("created_at"),
        updated_at=raw.get("updated_at") or raw.get("date"),
        url=raw.get("url"),
        metadata={"to": raw.get("to"), "labels": raw.get("labels", []), "has_attachment": bool(raw.get("has_attachment"))},
    )


def normalize_calendar_event(raw: dict[str, Any], source: str = "calendar") -> NormalizedRecord:
    title = clean_text(raw.get("title") or raw.get("summary") or "Ohne Titel")
    description = clean_text(raw.get("description") or "")
    location = clean_text(raw.get("location") or "")
    start = raw.get("start") or raw.get("start_time")
    end = raw.get("end") or raw.get("end_time")
    external_id = str(raw.get("id") or stable_hash(title + str(start) + str(end)))
    body = "\n".join(part for part in [description, f"Ort: {location}" if location else "", f"Start: {start}" if start else "", f"Ende: {end}" if end else ""] if part)
    return NormalizedRecord(
        source=source,
        external_id=external_id,
        title=title,
        body=body,
        record_type="calendar_event",
        created_at=start,
        updated_at=raw.get("updated_at"),
        url=raw.get("url"),
        metadata={"start": start, "end": end, "location": location, "attendees": raw.get("attendees", [])},
    )


def normalize_document(raw: dict[str, Any], source: str = "document") -> NormalizedRecord:
    title = clean_text(raw.get("title") or raw.get("name") or "Unbenannt")
    body = clean_text(raw.get("text") or raw.get("body") or raw.get("content") or "")
    external_id = str(raw.get("id") or raw.get("path") or stable_hash(title + body))
    return NormalizedRecord(
        source=source,
        external_id=external_id,
        title=title,
        body=body,
        record_type="document",
        author=raw.get("owner") or raw.get("author"),
        created_at=raw.get("created_at"),
        updated_at=raw.get("modified_at") or raw.get("updated_at"),
        url=raw.get("url") or raw.get("path"),
        metadata={"mime_type": raw.get("mime_type"), "size": raw.get("size")},
    )
