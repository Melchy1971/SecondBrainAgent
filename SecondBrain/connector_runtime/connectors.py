"""Concrete connectors.

The local-folder connector is fully self-contained. The network connectors
(Gmail, Drive, Calendar, GitHub) contain the real parsing, document-shaping, and
incremental-cursor logic; the raw HTTP transport is an injected ``client`` seam so
the same code runs in production (real client) and tests (fake client that can
raise simulated API errors). Connectors never read tokens themselves - the runtime
resolves the token from the vault and passes it in.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from secondbrain.connector_runtime.models import Document, FetchPage

_TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".log", ".csv"}


class Connector(Protocol):
    name: str
    requires_auth: bool

    def fetch(self, cursor: str | None, *, token: str | None) -> FetchPage:
        ...


class LocalFolderConnector:
    """Real connector: indexes text files under a folder, incrementally by mtime."""

    requires_auth = False

    def __init__(self, source_id: str, root: str | Path, *, suffixes: set[str] | None = None) -> None:
        self.name = "local_folder"
        self.source_id = source_id
        self.root = Path(root)
        self.suffixes = suffixes or _TEXT_SUFFIXES

    def fetch(self, cursor: str | None, *, token: str | None = None) -> FetchPage:
        since = float(cursor) if cursor else 0.0
        docs: list[Document] = []
        newest = since
        if self.root.exists():
            for path in sorted(self.root.rglob("*")):
                if not path.is_file() or path.suffix.lower() not in self.suffixes:
                    continue
                mtime = path.stat().st_mtime
                newest = max(newest, mtime)
                if mtime <= since:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                docs.append(Document(
                    external_id=str(path.relative_to(self.root)),
                    source_id=self.source_id,
                    connector=self.name,
                    kind="file",
                    title=path.name,
                    text=text,
                    metadata={"path": str(path), "bytes": path.stat().st_size},
                    updated_at=mtime,
                ))
        return FetchPage(documents=docs, cursor=str(newest), has_more=False)


class _ClientConnector:
    """Base for network connectors driven by an injected client."""

    requires_auth = True

    def __init__(self, name: str, source_id: str, client: Any) -> None:
        self.name = name
        self.source_id = source_id
        self.client = client

    def _doc(self, external_id: str, kind: str, title: str, text: str, updated_at: float, meta: dict) -> Document:
        return Document(external_id=str(external_id), source_id=self.source_id, connector=self.name,
                        kind=kind, title=title or "(untitled)", text=text or "", metadata=meta, updated_at=updated_at)


class GmailConnector(_ClientConnector):
    def __init__(self, source_id: str, client: Any) -> None:
        super().__init__("gmail", source_id, client)

    def fetch(self, cursor: str | None, *, token: str | None) -> FetchPage:
        page = self.client.list_messages(token=token, cursor=cursor)
        docs = []
        for msg in page.get("messages", []):
            body = "\n".join(filter(None, [msg.get("subject", ""), msg.get("from", ""), msg.get("snippet", "")]))
            docs.append(self._doc(msg["id"], "email", msg.get("subject", ""), body,
                                   float(msg.get("internalDate", 0)) / 1000.0 if msg.get("internalDate") else 0.0,
                                   {"from": msg.get("from"), "thread": msg.get("threadId")}))
        return FetchPage(documents=docs, cursor=page.get("next_cursor"), has_more=bool(page.get("has_more")))


class GoogleDriveConnector(_ClientConnector):
    def __init__(self, source_id: str, client: Any) -> None:
        super().__init__("google_drive", source_id, client)

    def fetch(self, cursor: str | None, *, token: str | None) -> FetchPage:
        page = self.client.list_files(token=token, cursor=cursor)
        docs = []
        for f in page.get("files", []):
            docs.append(self._doc(f["id"], "file", f.get("name", ""), f.get("content", ""),
                                   _parse_iso(f.get("modifiedTime")), {"mimeType": f.get("mimeType")}))
        return FetchPage(documents=docs, cursor=page.get("next_cursor"), has_more=bool(page.get("has_more")))


class GoogleCalendarConnector(_ClientConnector):
    def __init__(self, source_id: str, client: Any) -> None:
        super().__init__("google_calendar", source_id, client)

    def fetch(self, cursor: str | None, *, token: str | None) -> FetchPage:
        page = self.client.list_events(token=token, cursor=cursor)
        docs = []
        for e in page.get("events", []):
            body = "\n".join(filter(None, [e.get("summary", ""), e.get("description", ""), str(e.get("start", ""))]))
            docs.append(self._doc(e["id"], "event", e.get("summary", ""), body,
                                   _parse_iso(e.get("updated")), {"start": e.get("start"), "location": e.get("location")}))
        return FetchPage(documents=docs, cursor=page.get("next_cursor"), has_more=bool(page.get("has_more")))


class GitHubConnector(_ClientConnector):
    def __init__(self, source_id: str, client: Any) -> None:
        super().__init__("github", source_id, client)

    def fetch(self, cursor: str | None, *, token: str | None) -> FetchPage:
        page = self.client.list_items(token=token, cursor=cursor)
        docs = []
        for it in page.get("items", []):
            body = "\n".join(filter(None, [it.get("title", ""), it.get("body", "")]))
            docs.append(self._doc(it["id"], it.get("type", "issue"), it.get("title", ""), body,
                                   _parse_iso(it.get("updated_at")), {"repo": it.get("repo"), "url": it.get("url")}))
        return FetchPage(documents=docs, cursor=page.get("next_cursor"), has_more=bool(page.get("has_more")))


def _parse_iso(value: str | None) -> float:
    if not value:
        return 0.0
    from datetime import datetime
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0
