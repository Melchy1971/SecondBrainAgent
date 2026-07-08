"""Outlook Mail connector + approval-gated writer."""

from __future__ import annotations

from secondbrain.connectors.microsoft import normalizers
from secondbrain.connectors.microsoft.resources.base import GraphResourceConnector, GraphWriter

NAME = "m365_mail"
ENDPOINT = "me/messages"


def connector(client) -> GraphResourceConnector:
    return GraphResourceConnector(NAME, ENDPOINT, normalizers.mail_message, client, delta=True)


class MailWriter(GraphWriter):
    resource = "mail"

    def send(self, to: list[str], subject: str, body_html: str, *, save_to_sent: bool = True):
        payload = {
            "message": {
                "subject": subject,
                "body": {"contentType": "HTML", "content": body_html},
                "toRecipients": [{"emailAddress": {"address": a}} for a in to],
            },
            "saveToSentItems": save_to_sent,
        }
        return self._guarded("mail.send", "POST", ",".join(to), payload,
                             lambda: self.client.post("me/sendMail", payload))

    def create_draft(self, to: list[str], subject: str, body_html: str):
        payload = {
            "subject": subject,
            "body": {"contentType": "HTML", "content": body_html},
            "toRecipients": [{"emailAddress": {"address": a}} for a in to],
        }
        return self._guarded("mail.draft", "POST", ",".join(to), payload,
                             lambda: self.client.post("me/messages", payload))

    def delete(self, message_id: str):
        return self._guarded("mail.delete", "DELETE", message_id, {"id": message_id},
                             lambda: self.client.delete(f"me/messages/{message_id}"))
