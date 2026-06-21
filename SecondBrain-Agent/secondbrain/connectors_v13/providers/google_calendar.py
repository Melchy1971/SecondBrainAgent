class GoogleCalendarConnector:
    id = "google_calendar"

    def fetch_delta(self, cursor=None) -> list[dict]:
        return [
            {"type": "calendar_event", "id": "gcal-demo-1", "title": "Demo Termin", "cursor": cursor}
        ]
