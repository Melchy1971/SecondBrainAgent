"""v30.4 - Google Drive sync service."""

from __future__ import annotations

from secondbrain.connectors.sync_models import SyncItem, SyncResult


class GoogleDriveSyncService:
    connector = "google_drive"

    def __init__(self, client, checkpoint_store=None):
        self.client = client
        self.checkpoint_store = checkpoint_store

    def sync(self, cursor: str | None = None, limit: int = 100) -> SyncResult:
        response = self.client.list_changes(page_token=cursor, page_size=limit)
        changes = response.get("changes", [])
        items = [
            SyncItem(
                external_id=change.get("fileId") or change.get("id"),
                source=self.connector,
                kind="drive_change",
                payload=change,
            )
            for change in changes
        ]
        next_cursor = response.get("newStartPageToken") or response.get("nextPageToken")
        if self.checkpoint_store and next_cursor:
            self.checkpoint_store.save_checkpoint(self.connector, next_cursor)
        return SyncResult(self.connector, "PASS", len(items), next_cursor)
