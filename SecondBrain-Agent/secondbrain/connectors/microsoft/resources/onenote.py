"""OneNote connector (watermark) + approval-gated writer."""

from __future__ import annotations

from secondbrain.connectors.microsoft import normalizers
from secondbrain.connectors.microsoft.resources.base import GraphResourceConnector, GraphWriter

NAME = "m365_onenote"
ENDPOINT = "me/onenote/pages"


def connector(client) -> GraphResourceConnector:
    # OneNote pages have no delta endpoint -> incremental via lastModifiedDateTime watermark.
    return GraphResourceConnector(NAME, ENDPOINT, normalizers.onenote_page, client, delta=False)


class OneNoteWriter(GraphWriter):
    resource = "onenote"

    def create_page(self, section_id: str, title: str, body_html: str):
        html = f"<!DOCTYPE html><html><head><title>{title}</title></head><body>{body_html}</body></html>"
        target = f"me/onenote/sections/{section_id}/pages"
        return self._guarded("onenote.create", "POST", section_id, {"title": title},
                             lambda: self.client.request("POST", target, raw_body=html.encode("utf-8"),
                                                         headers={"Content-Type": "text/html"}))
