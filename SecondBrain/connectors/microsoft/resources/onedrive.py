"""OneDrive connector + approval-gated writer."""

from __future__ import annotations

from secondbrain.connectors.microsoft import normalizers
from secondbrain.connectors.microsoft.resources.base import GraphResourceConnector, GraphWriter

NAME = "m365_onedrive"
ENDPOINT = "me/drive/root"


def connector(client) -> GraphResourceConnector:
    # /me/drive/root/delta enumerates the whole drive incrementally.
    return GraphResourceConnector(NAME, ENDPOINT, normalizers.drive_item, client, delta=True)


class OneDriveWriter(GraphWriter):
    resource = "onedrive"

    def upload_text(self, path: str, content: str):
        target = f"me/drive/root:/{path.lstrip('/')}:/content"
        payload = {"path": path, "bytes": len(content)}
        return self._guarded("onedrive.upload", "PUT", path, payload,
                             lambda: self._put_text(target, content))

    def _put_text(self, target: str, content: str):
        # Raw (non-JSON) PUT of file content via the client's retry-aware request path.
        return self.client.request("PUT", target, raw_body=content.encode("utf-8"),
                                   headers={"Content-Type": "text/plain"})

    def create_folder(self, name: str, parent_path: str = ""):
        parent = f"me/drive/root:/{parent_path.strip('/')}:" if parent_path else "me/drive/root"
        payload = {"name": name, "folder": {}, "@microsoft.graph.conflictBehavior": "rename"}
        return self._guarded("onedrive.mkdir", "POST", f"{parent_path}/{name}", payload,
                             lambda: self.client.post(f"{parent}/children", payload))

    def delete(self, item_id: str):
        return self._guarded("onedrive.delete", "DELETE", item_id, {"id": item_id},
                             lambda: self.client.delete(f"me/drive/items/{item_id}"))
