"""Map Google API payloads to normalized ConnectorItem instances."""

from __future__ import annotations

from typing import Any, Mapping

from secondbrain.connectors.adapter_contract import ConnectorItem, parse_datetime


def _headers(msg: Mapping[str, Any]) -> dict[str, str]:
    out = {}
    for h in (msg.get("payload", {}) or {}).get("headers", []) or []:
        out[h.get("name", "").lower()] = h.get("value", "")
    return out


def gmail_message(p: Mapping[str, Any]) -> ConnectorItem | None:
    h = _headers(p)
    internal = p.get("internalDate")
    updated = int(internal) / 1000 if internal else 0
    body = p.get("snippet") or ""
    return ConnectorItem(
        external_id=str(p.get("id", "")),
        source="google_gmail",
        title=h.get("subject") or "(no subject)",
        content=str(body),
        updated_at=parse_datetime(updated),
        metadata={"from": h.get("from"), "threadId": p.get("threadId"), "labels": p.get("labelIds")},
    )


def calendar_event(p: Mapping[str, Any]) -> ConnectorItem | None:
    if p.get("status") == "cancelled":
        return None
    start = (p.get("start") or {}).get("dateTime") or (p.get("start") or {}).get("date")
    return ConnectorItem(
        external_id=str(p.get("id", "")),
        source="google_calendar",
        title=str(p.get("summary") or "(no title)"),
        content=str(p.get("description") or p.get("summary") or ""),
        updated_at=parse_datetime(p.get("updated") or 0),
        uri=p.get("htmlLink"),
        metadata={"start": start, "location": p.get("location"), "status": p.get("status")},
    )


def drive_change(p: Mapping[str, Any]) -> ConnectorItem | None:
    if p.get("removed"):
        return None
    f = p.get("file") or {}
    if not f.get("id"):
        return None
    return ConnectorItem(
        external_id=str(f.get("id", "")),
        source="google_drive",
        title=str(f.get("name") or "(file)"),
        content=str(f.get("name") or ""),
        updated_at=parse_datetime(f.get("modifiedTime") or 0),
        uri=f.get("webViewLink"),
        mime_type=f.get("mimeType"),
        metadata={"driveId": p.get("driveId")},
    )


def person(p: Mapping[str, Any]) -> ConnectorItem | None:
    names = p.get("names") or []
    display = names[0].get("displayName") if names else None
    emails = [e.get("value") for e in (p.get("emailAddresses") or []) if e.get("value")]
    name = display or (emails[0] if emails else "(contact)")
    return ConnectorItem(
        external_id=str(p.get("resourceName", "")),
        source="google_contacts",
        title=str(name),
        content=", ".join(emails) or str(name),
        updated_at=parse_datetime((p.get("metadata") or {}).get("sources", [{}])[0].get("updateTime") or 0),
        metadata={"emails": emails},
    )


def task(p: Mapping[str, Any]) -> ConnectorItem | None:
    if p.get("deleted"):
        return None
    return ConnectorItem(
        external_id=str(p.get("id", "")),
        source="google_tasks",
        title=str(p.get("title") or "(task)"),
        content=str(p.get("notes") or p.get("title") or ""),
        updated_at=parse_datetime(p.get("updated") or 0),
        metadata={"status": p.get("status"), "due": p.get("due")},
    )
