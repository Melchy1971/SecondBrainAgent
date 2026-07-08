"""P5 v23.1 - Notification Center."""

class NotificationCenter:
    def __init__(self):
        self._notifications = []

    def push(self, title: str, message: str):
        self._notifications.append({
            "title": title,
            "message": message,
        })

    def list(self):
        return list(self._notifications)
