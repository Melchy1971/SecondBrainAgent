"""Gmail connector (list + fetch, internalDate watermark) + approval-gated writer."""

from __future__ import annotations

import base64
from email.message import EmailMessage

from secondbrain.connectors.incremental_runner import FetchBatch, FetchedItem
from secondbrain.connectors.google import normalizers
from secondbrain.connectors.google.client import GMAIL_LIST_PAGING
from secondbrain.connectors.google.resources.base import GoogleWriter

NAME = "google_gmail"
LIST_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"


class GmailConnector:
    name = NAME

    def __init__(self, client, *, max_messages: int = 50):
        self.client = client
        self.max_messages = max_messages

    def fetch_since(self, cursor, limit):
        params = {"maxResults": min(limit, self.max_messages)}
        if cursor:
            params["q"] = f"after:{cursor}"
        listing, _ = self.client.follow_collection(LIST_URL, params=params, delta=False, paging=GMAIL_LIST_PAGING)
        items = []
        newest = int(cursor) if cursor else 0
        for ref in listing[: self.max_messages]:
            msg = self.client.get(f"{LIST_URL}/{ref['id']}", params={"format": "metadata",
                                  "metadataHeaders": "Subject"})
            ci = normalizers.gmail_message(msg)
            if ci is None:
                continue
            internal = int(msg.get("internalDate", 0)) // 1000
            newest = max(newest, internal)
            items.append(FetchedItem(id=ci.external_id, payload=ci, cursor=str(newest)))
        return FetchBatch(items, next_cursor=str(newest) if newest else cursor, has_more=False)


def connector(client):
    return GmailConnector(client)


class GmailWriter(GoogleWriter):
    resource = "google_gmail"

    def send(self, to, subject, body_text):
        msg = EmailMessage()
        msg["To"] = ", ".join(to)
        msg["Subject"] = subject
        msg.set_content(body_text)
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
        payload = {"raw": raw}
        return self._guarded("gmail.send", "POST", ",".join(to), {"to": to, "subject": subject},
                             lambda: self.client.post(SEND_URL, payload))
