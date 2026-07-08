"""P4 v22.0 - Base Connector."""

class BaseConnector:
    name = "base"

    def health(self):
        return {"status": "PASS", "connector": self.name}

    def sync(self):
        return {"status": "PASS", "items": 0}
