from datetime import datetime, timezone
from .models import MobileDevice
from .store import JsonStore


class DeviceRegistry:
    def __init__(self, store: JsonStore):
        self.store = store

    def list_devices(self) -> list[dict]:
        return self.store.load("devices", [])

    def register(self, device_id: str, name: str, platform: str, trusted: bool = False, biometric: bool = False) -> dict:
        devices = self.list_devices()
        existing = next((d for d in devices if d["id"] == device_id), None)
        payload = MobileDevice(
            id=device_id,
            name=name,
            platform=platform,
            trusted=trusted,
            biometric_enabled=biometric,
            last_seen=datetime.now(timezone.utc).isoformat(),
        ).to_dict()
        if existing:
            devices = [payload if d["id"] == device_id else d for d in devices]
        else:
            devices.append(payload)
        self.store.save("devices", devices)
        return payload

    def is_trusted(self, device_id: str) -> bool:
        return any(d["id"] == device_id and d.get("trusted") for d in self.list_devices())
