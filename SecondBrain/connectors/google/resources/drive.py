"""Google Drive connector (changes API delta) + approval-gated writer."""

from __future__ import annotations

from secondbrain.connectors.incremental_runner import FetchBatch, FetchedItem
from secondbrain.connectors.google import normalizers
from secondbrain.connectors.google.client import DRIVE_CHANGES_PAGING
from secondbrain.connectors.google.resources.base import GoogleWriter

NAME = "google_drive"
CHANGES_URL = "drive/v3/changes"
START_URL = "drive/v3/changes/startPageToken"
FILES_UPLOAD = "https://www.googleapis.com/upload/drive/v3/files?uploadType=media"


class DriveConnector:
    name = NAME

    def __init__(self, client):
        self.client = client

    def fetch_since(self, cursor, limit):
        token = cursor
        if not token:
            token = self.client.get(START_URL).get("startPageToken")
        params = {"pageToken": token, "pageSize": limit,
                  "fields": "changes(removed,file(id,name,mimeType,modifiedTime,webViewLink)),nextPageToken,newStartPageToken"}
        raw, delta = self.client.follow_collection(CHANGES_URL, params=params, delta=True, paging=DRIVE_CHANGES_PAGING)
        items = []
        for change in raw:
            ci = normalizers.drive_change(change)
            if ci is None:
                continue
            items.append(FetchedItem(id=ci.external_id, payload=ci, cursor=delta or token))
        return FetchBatch(items, next_cursor=delta or token, has_more=False)


def connector(client):
    return DriveConnector(client)


class DriveWriter(GoogleWriter):
    resource = "google_drive"

    def upload_text(self, name, content):
        return self._guarded("gdrive.upload", "POST", name, {"name": name, "bytes": len(content)},
                             lambda: self.client.request("POST", f"{FILES_UPLOAD}&name={name}",
                                                         raw_body=content.encode("utf-8"),
                                                         headers={"Content-Type": "text/plain"}))

    def delete(self, file_id):
        return self._guarded("gdrive.delete", "DELETE", file_id, {"id": file_id},
                             lambda: self.client.delete(f"drive/v3/files/{file_id}"))
