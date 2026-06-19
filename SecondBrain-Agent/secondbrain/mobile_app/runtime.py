from .store import JsonStore
from .registry import DeviceRegistry
from .offline_queue import OfflineQueue
from .push import PushOutbox
from .widgets import MobileWidgetRegistry
from .sync import MobileSyncProtocol


class MobileAppRuntime:
    def __init__(self, root="."):
        self.store = JsonStore(root)
        self.devices = DeviceRegistry(self.store)
        self.queue = OfflineQueue(self.store)
        self.push = PushOutbox(self.store)
        self.widgets = MobileWidgetRegistry(self.store)
        self.syncer = MobileSyncProtocol(self.store)

    def status(self) -> dict:
        return {
            "devices": len(self.devices.list_devices()),
            "trusted_devices": sum(1 for d in self.devices.list_devices() if d.get("trusted")),
            "widgets": len(self.widgets.widgets()),
            "sync": self.syncer.status(),
        }

    def secure_command(self, device_id: str, command: str, payload: dict) -> dict:
        if not self.devices.is_trusted(device_id):
            return {"ok": False, "error": "device_not_trusted", "device_id": device_id}
        return {"ok": True, "queued": self.queue.enqueue(device_id, command, payload)}
