"""Google Calendar connector (syncToken delta) + approval-gated writer."""

from __future__ import annotations

from secondbrain.connectors.scaffold.delta_connector import DeltaCollectionConnector
from secondbrain.connectors.scaffold.rest_client import GOOGLE_PAGING
from secondbrain.connectors.google import normalizers
from secondbrain.connectors.google.resources.base import GoogleWriter

NAME = "google_calendar"
ENDPOINT = "calendar/v3/calendars/primary/events"


def connector(client):
    return DeltaCollectionConnector(
        NAME, ENDPOINT, normalizers.calendar_event, client,
        delta_mode="sync_token_param", sync_param="syncToken",
        params={"showDeleted": "true", "singleEvents": "true"}, paging=GOOGLE_PAGING,
    )


class CalendarWriter(GoogleWriter):
    resource = "google_calendar"

    def create_event(self, summary, start_iso, end_iso, *, description=""):
        payload = {"summary": summary, "description": description,
                   "start": {"dateTime": start_iso}, "end": {"dateTime": end_iso}}
        return self._guarded("gcal.create", "POST", summary, payload,
                             lambda: self.client.post(ENDPOINT, payload))

    def delete_event(self, event_id):
        return self._guarded("gcal.delete", "DELETE", event_id, {"id": event_id},
                             lambda: self.client.delete(f"{ENDPOINT}/{event_id}"))
