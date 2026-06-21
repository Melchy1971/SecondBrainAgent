class PaperlessConnector:
    id = "paperless"

    def fetch_delta(self, cursor=None) -> list[dict]:
        return [
            {"type": "document", "id": "paperless-demo-1", "title": "Demo Dokument", "cursor": cursor}
        ]
