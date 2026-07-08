"""Map raw Graph payloads to normalized ConnectorItem instances.

Returns None for delta tombstones (@removed) so the sync pipeline skips them.
"""

from __future__ import annotations

from typing import Any, Mapping

from secondbrain.connectors.adapter_contract import ConnectorItem, parse_datetime


def _updated(payload: Mapping[str, Any]) -> Any:
    return payload.get("lastModifiedDateTime") or payload.get("receivedDateTime") \
        or payload.get("createdDateTime") or payload.get("createdDateTime")


def _removed(payload: Mapping[str, Any]) -> bool:
    return "@removed" in payload


def mail_message(p: Mapping[str, Any]) -> ConnectorItem | None:
    if _removed(p):
        return None
    body = (p.get("body") or {}).get("content") or p.get("bodyPreview") or ""
    sender = ((p.get("from") or {}).get("emailAddress") or {}).get("address", "")
    return ConnectorItem(
        external_id=str(p.get("id", "")),
        source="m365_mail",
        title=str(p.get("subject") or "(no subject)"),
        content=str(body),
        updated_at=parse_datetime(_updated(p) or p.get("sentDateTime") or 0),
        uri=p.get("webLink"),
        metadata={"from": sender, "isRead": p.get("isRead"), "conversationId": p.get("conversationId")},
    )


def calendar_event(p: Mapping[str, Any]) -> ConnectorItem | None:
    if _removed(p):
        return None
    body = (p.get("body") or {}).get("content") or p.get("bodyPreview") or ""
    return ConnectorItem(
        external_id=str(p.get("id", "")),
        source="m365_calendar",
        title=str(p.get("subject") or "(no title)"),
        content=str(body),
        updated_at=parse_datetime(_updated(p) or 0),
        uri=p.get("webLink"),
        metadata={"start": (p.get("start") or {}).get("dateTime"),
                  "end": (p.get("end") or {}).get("dateTime"),
                  "location": (p.get("location") or {}).get("displayName")},
    )


def contact(p: Mapping[str, Any]) -> ConnectorItem | None:
    if _removed(p):
        return None
    emails = [e.get("address") for e in (p.get("emailAddresses") or []) if e.get("address")]
    name = p.get("displayName") or " ".join(filter(None, [p.get("givenName"), p.get("surname")])) or "(contact)"
    return ConnectorItem(
        external_id=str(p.get("id", "")),
        source="m365_contacts",
        title=str(name),
        content=", ".join(emails) or str(name),
        updated_at=parse_datetime(_updated(p) or 0),
        metadata={"emails": emails, "company": p.get("companyName")},
    )


def drive_item(p: Mapping[str, Any]) -> ConnectorItem | None:
    if _removed(p):
        return None
    kind = "folder" if "folder" in p else "file"
    return ConnectorItem(
        external_id=str(p.get("id", "")),
        source="m365_onedrive",
        title=str(p.get("name") or "(item)"),
        content=str(p.get("name") or ""),
        updated_at=parse_datetime(_updated(p) or 0),
        uri=p.get("webUrl"),
        mime_type=(p.get("file") or {}).get("mimeType"),
        metadata={"kind": kind, "size": p.get("size"),
                  "parent": (p.get("parentReference") or {}).get("path")},
    )


def teams_message(p: Mapping[str, Any]) -> ConnectorItem | None:
    if _removed(p) or p.get("messageType") == "systemEventMessage":
        return None
    body = (p.get("body") or {}).get("content") or ""
    author = (((p.get("from") or {}).get("user")) or {}).get("displayName", "")
    if not body.strip():
        return None
    return ConnectorItem(
        external_id=str(p.get("id", "")),
        source="m365_teams",
        title=f"Teams message from {author or 'unknown'}",
        content=str(body),
        updated_at=parse_datetime(_updated(p) or 0),
        uri=p.get("webUrl"),
        metadata={"author": author, "chatId": p.get("chatId"), "channelId": (p.get("channelIdentity") or {}).get("channelId")},
    )


def todo_task(p: Mapping[str, Any]) -> ConnectorItem | None:
    if _removed(p):
        return None
    body = (p.get("body") or {}).get("content") or ""
    return ConnectorItem(
        external_id=str(p.get("id", "")),
        source="m365_todo",
        title=str(p.get("title") or "(task)"),
        content=str(body or p.get("title") or ""),
        updated_at=parse_datetime(_updated(p) or 0),
        metadata={"status": p.get("status"), "importance": p.get("importance"),
                  "dueDateTime": (p.get("dueDateTime") or {}).get("dateTime")},
    )


def onenote_page(p: Mapping[str, Any]) -> ConnectorItem | None:
    if _removed(p):
        return None
    return ConnectorItem(
        external_id=str(p.get("id", "")),
        source="m365_onenote",
        title=str(p.get("title") or "(page)"),
        content=str(p.get("title") or ""),
        updated_at=parse_datetime(_updated(p) or 0),
        uri=p.get("links", {}).get("oneNoteWebUrl", {}).get("href") if isinstance(p.get("links"), dict) else p.get("contentUrl"),
        metadata={"contentUrl": p.get("contentUrl"), "notebook": p.get("parentNotebook", {}).get("displayName") if isinstance(p.get("parentNotebook"), dict) else None},
    )
