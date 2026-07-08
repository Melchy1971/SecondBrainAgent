"""Microsoft To Do connector (per-list delta) + approval-gated writer."""

from __future__ import annotations

import json

from secondbrain.connectors.incremental_runner import FetchBatch, FetchedItem
from secondbrain.connectors.microsoft import normalizers
from secondbrain.connectors.microsoft.resources.base import GraphWriter

NAME = "m365_todo"


class TodoConnector:
    """Walks every To Do list with an independent delta cursor.

    The connector cursor is a JSON map {listId: deltaLink}, opaque to the runner.
    """

    name = NAME

    def __init__(self, client) -> None:
        self.client = client

    def fetch_since(self, cursor: str | None, limit: int) -> FetchBatch:
        cursor_map = json.loads(cursor) if cursor else {}
        lists, _ = self.client.follow_collection("me/todo/lists", params={"$top": 50}, delta=False)
        new_map: dict[str, str] = {}
        items: list[FetchedItem] = []
        for lst in lists:
            list_id = lst.get("id")
            if not list_id:
                continue
            start = cursor_map.get(list_id) or f"me/todo/lists/{list_id}/tasks/delta"
            params = None if cursor_map.get(list_id) else {"$top": limit}
            raw, delta_link = self.client.follow_collection(start, params=params, delta=True)
            if delta_link:
                new_map[list_id] = delta_link
            elif cursor_map.get(list_id):
                new_map[list_id] = cursor_map[list_id]
            for payload in raw:
                citem = normalizers.todo_task(payload)
                if citem is None:
                    continue
                items.append(FetchedItem(id=citem.external_id, payload=citem, cursor=None))
        next_cursor = json.dumps(new_map, sort_keys=True) if new_map else cursor
        return FetchBatch(items=items, next_cursor=next_cursor, has_more=False)


def connector(client) -> TodoConnector:
    return TodoConnector(client)


class TodoWriter(GraphWriter):
    resource = "todo"

    def create_task(self, list_id: str, title: str, *, body_text: str = ""):
        payload = {"title": title, "body": {"contentType": "text", "content": body_text}}
        return self._guarded("todo.create", "POST", list_id, payload,
                             lambda: self.client.post(f"me/todo/lists/{list_id}/tasks", payload))

    def complete_task(self, list_id: str, task_id: str):
        payload = {"status": "completed"}
        return self._guarded("todo.complete", "PATCH", f"{list_id}/{task_id}", payload,
                             lambda: self.client.patch(f"me/todo/lists/{list_id}/tasks/{task_id}", payload))
