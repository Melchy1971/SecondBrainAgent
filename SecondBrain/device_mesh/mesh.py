from datetime import datetime, timezone
from uuid import uuid4


class DeviceMesh:
    def __init__(self, store):
        self.store = store

    def devices(self) -> list[dict]:
        return self.store.load("devices", [])

    def register_device(self, name: str, platform: str, capabilities: list[str] | None = None, trust_level: str = "untrusted") -> dict:
        device = {
            "id": str(uuid4()),
            "name": name,
            "platform": platform,
            "capabilities": capabilities or [],
            "trust_level": trust_level,
            "paired": trust_level != "untrusted",
            "last_seen": datetime.now(timezone.utc).isoformat(),
        }
        return self.store.append("devices", device)

    def pair_request(self, device_name: str, platform: str) -> dict:
        request = {
            "id": str(uuid4()),
            "device_name": device_name,
            "platform": platform,
            "status": "pending",
            "pairing_code": str(uuid4())[:8],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.store.append("pairing_requests", request)

    def approve_pairing(self, request_id: str) -> dict:
        requests = self.store.load("pairing_requests", [])
        approved = None
        updated = []
        for req in requests:
            if req["id"] == request_id:
                req = {**req, "status": "approved", "approved_at": datetime.now(timezone.utc).isoformat()}
                approved = req
            updated.append(req)
        self.store.save("pairing_requests", updated)
        if not approved:
            return {"ok": False, "error": "pairing_request_not_found"}
        device = self.register_device(approved["device_name"], approved["platform"], ["sync", "push", "capture"], "trusted")
        return {"ok": True, "request": approved, "device": device}

    def pairing_requests(self) -> list[dict]:
        return self.store.load("pairing_requests", [])
