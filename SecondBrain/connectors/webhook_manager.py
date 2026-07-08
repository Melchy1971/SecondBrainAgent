"""P4 v22.2 - Webhook Infrastructure."""

class WebhookManager:
    def __init__(self):
        self._webhooks = {}

    def register(self, connector: str, url: str):
        self._webhooks[connector] = url

    def get(self, connector: str):
        return self._webhooks.get(connector)
