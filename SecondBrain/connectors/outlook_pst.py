"""Outlook PST connector. Real PST parsing via pypff (lazy, integration-only).

pypff (libpff) is an optional native dependency; a FakePstReader powers offline tests.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Protocol, runtime_checkable

from secondbrain.connectors.incremental_runner import FetchBatch, FetchedItem
from secondbrain.connectors.adapter_contract import ConnectorItem, parse_datetime


@runtime_checkable
class PstReader(Protocol):
    def iter_messages(self) -> Iterable[dict]: ...


class PypffPstReader:
    def __init__(self, path: str) -> None:
        try:
            import pypff  # noqa: F401
        except Exception as exc:  # pragma: no cover - optional native dep
            raise RuntimeError("Outlook PST parsing requires 'pypff' (libpff). Install it on the host.") from exc
        import pypff
        self._pff = pypff.file()
        self._pff.open(path)

    def iter_messages(self):  # pragma: no cover - integration
        def walk(folder, path=""):
            for i in range(folder.number_of_sub_messages):
                m = folder.get_sub_message(i)
                yield {"id": str(getattr(m, "identifier", i)),
                       "subject": m.subject or "", "body": m.plain_text_body or "",
                       "sender": getattr(m, "sender_name", ""), "folder": path,
                       "received": str(getattr(m, "delivery_time", ""))}
            for j in range(folder.number_of_sub_folders):
                sub = folder.get_sub_folder(j)
                yield from walk(sub, f"{path}/{sub.name}")
        yield from walk(self._pff.get_root_folder())


class FakePstReader:
    def __init__(self, messages: list[dict]) -> None:
        self._messages = messages

    def iter_messages(self):
        return list(self._messages)


class OutlookPstConnector:
    name = "outlook_pst"

    def __init__(self, reader: PstReader) -> None:
        self.reader = reader

    def fetch_since(self, cursor: str | None, limit: int) -> FetchBatch:
        items, newest = [], cursor
        for msg in self.reader.iter_messages():
            received = str(msg.get("received") or "")
            if cursor and received and received <= cursor:
                continue
            body = str(msg.get("body") or "")
            if not (msg.get("subject") or body):
                continue
            ci = ConnectorItem(
                external_id=str(msg.get("id")),
                source=self.name,
                title=str(msg.get("subject") or "(no subject)"),
                content=body or str(msg.get("subject")),
                updated_at=parse_datetime(received or datetime.now(timezone.utc)),
                metadata={"sender": msg.get("sender"), "folder": msg.get("folder")})
            if newest is None or (received and received > newest):
                newest = received
            items.append(FetchedItem(id=ci.external_id, payload=ci, cursor=received))
            if len(items) >= limit:
                break
        return FetchBatch(items=items, next_cursor=newest, has_more=False)
