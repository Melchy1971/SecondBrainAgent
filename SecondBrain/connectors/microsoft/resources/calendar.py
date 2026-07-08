"""Outlook Calendar connector + approval-gated writer."""

from __future__ import annotations

from secondbrain.connectors.microsoft import normalizers
from secondbrain.connectors.microsoft.resources.base import GraphResourceConnector, GraphWriter

NAME = "m365_calendar"
ENDPOINT = "me/calendarView"
# calendarView/delta requires a time window + change-tracking Prefer header.
DEFAULT_WINDOW = {"startDateTime": "2000-01-01T00:00:00Z", "endDateTime": "2100-01-01T00:00:00Z"}


def connector(client) -> GraphResourceConnector:
    return GraphResourceConnector(
        NAME, ENDPOINT, normalizers.calendar_event, client,
        delta=True, prefer="odata.track-changes", params=dict(DEFAULT_WINDOW),
    )


class CalendarWriter(GraphWriter):
    resource = "calendar"

    def create_event(self, subject: str, start_iso: str, end_iso: str, *, body_html: str = "", tz: str = "UTC"):
        payload = {
            "subject": subject,
            "body": {"contentType": "HTML", "content": body_html},
            "start": {"dateTime": start_iso, "timeZone": tz},
            "end": {"dateTime": end_iso, "timeZone": tz},
        }
        return self._guarded("calendar.create", "POST", subject, payload,
                             lambda: self.client.post("me/events", payload))

    def update_event(self, event_id: str, changes: dict):
        return self._guarded("calendar.update", "PATCH", event_id, changes,
                             lambda: self.client.patch(f"me/events/{event_id}", changes))

    def delete_event(self, event_id: str):
        return self._guarded("calendar.delete", "DELETE", event_id, {"id": event_id},
                             lambda: self.client.delete(f"me/events/{event_id}"))
