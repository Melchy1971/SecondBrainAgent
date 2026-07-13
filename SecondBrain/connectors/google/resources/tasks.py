"""Google Tasks connector (tasklists + updated watermark) + approval-gated writer."""

from __future__ import annotations

from secondbrain.connectors.incremental_runner import FetchBatch, FetchedItem
from secondbrain.connectors.scaffold.rest_client import GOOGLE_PAGING
from secondbrain.connectors.scaffold.delta_connector import max_watermark
from secondbrain.connectors.google import normalizers
from secondbrain.connectors.google.resources.base import GoogleWriter

NAME = "google_tasks"
LISTS_URL = "https://tasks.googleapis.com/tasks/v1/users/@me/lists"
TASKS_URL = "https://tasks.googleapis.com/tasks/v1/lists/{list_id}/tasks"


class TasksConnector:
    name = NAME

    def __init__(self, client):
        self.client = client

    def fetch_since(self, cursor, limit):
        lists = self.client.get(LISTS_URL, params={"maxResults": 100}).get("items", [])
        items = []
        newest = cursor
        for tl in lists:
            params = {"maxResults": limit, "showCompleted": "true"}
            if cursor:
                params["updatedMin"] = cursor
            raw, _ = self.client.follow_collection(TASKS_URL.format(list_id=tl["id"]),
                                                   params=params, delta=False, paging=GOOGLE_PAGING)
            newest = max_watermark(raw, "updated", newest)
            for t in raw:
                ci = normalizers.task(t)
                if ci is None:
                    continue
                items.append(FetchedItem(id=ci.external_id, payload=ci, cursor=newest))
        return FetchBatch(items, next_cursor=newest, has_more=False)


def connector(client):
    return TasksConnector(client)


class TasksWriter(GoogleWriter):
    resource = "google_tasks"

    def create_task(self, list_id, title, *, notes=""):
        payload = {"title": title, "notes": notes}
        return self._guarded("gtasks.create", "POST", list_id, payload,
                             lambda: self.client.post(TASKS_URL.format(list_id=list_id), payload))

    def complete_task(self, list_id, task_id):
        payload = {"status": "completed"}
        return self._guarded("gtasks.complete", "PATCH", f"{list_id}/{task_id}", payload,
                             lambda: self.client.patch(f"{TASKS_URL.format(list_id=list_id)}/{task_id}", payload))
