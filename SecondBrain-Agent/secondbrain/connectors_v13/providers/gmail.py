class GmailConnector:
    id = "gmail"

    def fetch_delta(self, cursor=None) -> list[dict]:
        return [
            {"type": "email", "id": "gmail-demo-1", "subject": "Demo Mail", "from": "demo@example.com", "cursor": cursor}
        ]
