from datetime import datetime, timezone


class WebRuntime:
    def __init__(self, store):
        self.store = store

    def manifest(self) -> dict:
        return {
            "name": "SecondBrain Web Runtime",
            "url": "https://jarvis.local",
            "modules": ["dashboard", "chat", "tasks", "projects", "knowledge", "calendar", "notifications", "settings"],
        }

    def start(self) -> dict:
        state = {"status": "running", "url": "https://jarvis.local", "started_at": datetime.now(timezone.utc).isoformat()}
        self.store.save("web_runtime", state)
        return state

    def status(self) -> dict:
        return self.store.load("web_runtime", {"status": "stopped", "url": "https://jarvis.local"})
