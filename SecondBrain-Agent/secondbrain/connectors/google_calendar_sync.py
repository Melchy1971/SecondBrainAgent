"""v30.4 - Google Calendar sync service."""

from __future__ import annotations

from secondbrain.connectors.sync_models import SyncItem, SyncResult


class GoogleCalendarSyncService:
    connector = "google_calendar"

    def __init__(self, client, checkpoint_store=None):
        self.client = client
        self.checkpoint_store = checkpoint_store

    def sync(self, cursor: str | None = None, limit: int = 250) -> SyncResult:
        response = self.client.list_events(sync_token=cursor, max_results=limit)
        events = response.get("items", [])
        items = [
            SyncItem(
                external_id=event["id"],
                source=self.connector,
                kind="calendar_event",
                payload=event,
            )
            for event in events
        ]
        next_cursor = response.get("nextSyncToken") or response.get("next_cursor")
        if self.checkpoint_store and next_cursor:
            self.checkpoint_store.save_checkpoint(self.connector, next_cursor)
        return SyncResult(self.connector, "PASS", len(items), next_cursor)
