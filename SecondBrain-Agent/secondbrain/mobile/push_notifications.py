"""P7 v25.0 - Push Notifications."""

class PushNotificationService:
    def __init__(self):
        self._messages = []

    def send(self, title: str, message: str):
        self._messages.append({"title": title, "message": message})

    def list(self):
        return list(self._messages)
