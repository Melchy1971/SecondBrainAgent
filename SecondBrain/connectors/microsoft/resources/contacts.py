"""Contacts connector + approval-gated writer."""

from __future__ import annotations

from secondbrain.connectors.microsoft import normalizers
from secondbrain.connectors.microsoft.resources.base import GraphResourceConnector, GraphWriter

NAME = "m365_contacts"
ENDPOINT = "me/contacts"


def connector(client) -> GraphResourceConnector:
    return GraphResourceConnector(NAME, ENDPOINT, normalizers.contact, client, delta=True)


class ContactsWriter(GraphWriter):
    resource = "contacts"

    def create(self, given_name: str, surname: str, emails: list[str]):
        payload = {
            "givenName": given_name,
            "surname": surname,
            "emailAddresses": [{"address": a, "name": f"{given_name} {surname}".strip()} for a in emails],
        }
        return self._guarded("contacts.create", "POST", ",".join(emails) or surname, payload,
                             lambda: self.client.post("me/contacts", payload))

    def delete(self, contact_id: str):
        return self._guarded("contacts.delete", "DELETE", contact_id, {"id": contact_id},
                             lambda: self.client.delete(f"me/contacts/{contact_id}"))
