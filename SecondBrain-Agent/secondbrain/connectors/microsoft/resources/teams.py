"""Teams messages connector (batch-based) + approval-gated writer."""

from __future__ import annotations

from secondbrain.connectors.incremental_runner import FetchBatch, FetchedItem
from secondbrain.connectors.microsoft import normalizers
from secondbrain.connectors.microsoft.resources.base import GraphWriter, _max_watermark

NAME = "m365_teams"


class TeamsConnector:
    """Aggregates recent messages across the user's chats using Graph $batch."""

    name = NAME

    def __init__(self, client, *, max_chats: int = 20) -> None:
        self.client = client
        self.max_chats = max_chats

    def fetch_since(self, cursor: str | None, limit: int) -> FetchBatch:
        chats, _ = self.client.follow_collection("me/chats", params={"$top": self.max_chats}, delta=False)
        chat_ids = [c["id"] for c in chats if c.get("id")]
        if not chat_ids:
            return FetchBatch(items=[], next_cursor=cursor, has_more=False)
        requests = [{"id": cid, "method": "GET", "url": f"/me/chats/{cid}/messages?$top={limit}"} for cid in chat_ids]
        responses = self.client.batch(requests)
        raw: list[dict] = []
        for resp in responses:
            if int(resp.get("status", 0)) // 100 == 2:
                raw.extend((resp.get("body") or {}).get("value", []))
        watermark = _max_watermark(raw, "lastModifiedDateTime", cursor)
        items: list[FetchedItem] = []
        for payload in raw:
            citem = normalizers.teams_message(payload)
            if citem is None:
                continue
            if cursor and str(payload.get("lastModifiedDateTime", "")) <= cursor:
                continue
            items.append(FetchedItem(id=citem.external_id, payload=citem, cursor=watermark))
        return FetchBatch(items=items, next_cursor=watermark, has_more=False)


def connector(client) -> TeamsConnector:
    return TeamsConnector(client)


class TeamsWriter(GraphWriter):
    resource = "teams"

    def post_chat_message(self, chat_id: str, body_html: str):
        payload = {"body": {"contentType": "html", "content": body_html}}
        return self._guarded("teams.chat_message", "POST", chat_id, payload,
                             lambda: self.client.post(f"me/chats/{chat_id}/messages", payload))

    def post_channel_message(self, team_id: str, channel_id: str, body_html: str):
        payload = {"body": {"contentType": "html", "content": body_html}}
        target = f"teams/{team_id}/channels/{channel_id}/messages"
        return self._guarded("teams.channel_message", "POST", f"{team_id}/{channel_id}", payload,
                             lambda: self.client.post(target, payload))
