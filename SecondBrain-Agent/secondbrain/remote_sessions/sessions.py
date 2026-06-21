from datetime import datetime, timezone
from uuid import uuid4


class RemoteSessionManager:
    def __init__(self, store):
        self.store = store

    def create(self, title: str, device_id: str | None = None, state: dict | None = None) -> dict:
        session = {
            "id": str(uuid4()),
            "title": title,
            "device_id": device_id,
            "state": state or {},
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.store.append("sessions", session)

    def sessions(self) -> list[dict]:
        return self.store.load("sessions", [])

    def resume(self, session_id: str, target_device_id: str) -> dict:
        for session in self.sessions():
            if session["id"] == session_id:
                resumed = {**session, "resumed_on": target_device_id, "resumed_at": datetime.now(timezone.utc).isoformat()}
                return self.store.append("session_resume_history", resumed)
        return {"ok": False, "error": "session_not_found"}
