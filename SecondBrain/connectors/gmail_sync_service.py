"""v30.4 - Gmail sync service."""

from __future__ import annotations

from secondbrain.connectors.sync_models import SyncItem, SyncResult


class GmailSyncService:
    connector = "gmail"

    def __init__(self, client, checkpoint_store=None):
        self.client = client
        self.checkpoint_store = checkpoint_store

    def sync(self, cursor: str | None = None, limit: int = 100) -> SyncResult:
        response = self.client.list_messages(cursor=cursor, limit=limit)
        messages = response.get("messages", [])
        items = [
            SyncItem(
                external_id=msg["id"],
                source=self.connector,
                kind="email",
                payload=msg,
                updated_at=float(msg.get("internalDate", 0) or 0),
            )
            for msg in messages
        ]
        next_cursor = response.get("historyId") or response.get("next_cursor")
        if self.checkpoint_store and next_cursor:
            self.checkpoint_store.save_checkpoint(self.connector, next_cursor)
        return SyncResult(self.connector, "PASS", len(items), next_cursor)
