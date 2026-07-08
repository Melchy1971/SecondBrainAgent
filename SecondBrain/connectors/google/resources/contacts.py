"""Google Contacts (People API, syncToken delta) + approval-gated writer."""

from __future__ import annotations

from secondbrain.connectors.scaffold.delta_connector import DeltaCollectionConnector
from secondbrain.connectors.google import normalizers
from secondbrain.connectors.google.client import CONTACTS_PAGING
from secondbrain.connectors.google.resources.base import GoogleWriter

NAME = "google_contacts"
ENDPOINT = "https://people.googleapis.com/v1/people/me/connections"


def connector(client):
    return DeltaCollectionConnector(
        NAME, ENDPOINT, normalizers.person, client,
        delta_mode="sync_token_param", sync_param="syncToken",
        params={"personFields": "names,emailAddresses", "requestSyncToken": "true"},
        paging=CONTACTS_PAGING,
    )


class ContactsWriter(GoogleWriter):
    resource = "google_contacts"

    def create(self, given_name, family_name, emails):
        payload = {"names": [{"givenName": given_name, "familyName": family_name}],
                   "emailAddresses": [{"value": e} for e in emails]}
        return self._guarded("gcontacts.create", "POST", ",".join(emails) or family_name, payload,
                             lambda: self.client.post("https://people.googleapis.com/v1/people:createContact", payload))
