from .store import JsonStore
from secondbrain.identity_service import IdentityService
from secondbrain.device_mesh import DeviceMesh
from secondbrain.sync_engine import SyncEngineV2
from secondbrain.push_service import PushService
from secondbrain.offline_engine import OfflineEngine
from secondbrain.remote_sessions import RemoteSessionManager
from secondbrain.widget_engine import WidgetEngine
from secondbrain.web_runtime import WebRuntime


class CompanionPlatform:
    def __init__(self, root="."):
        self.store = JsonStore(root)
        self.identity = IdentityService(self.store)
        self.devices = DeviceMesh(self.store)
        self.sync = SyncEngineV2(self.store)
        self.push = PushService(self.store)
        self.offline = OfflineEngine(self.store)
        self.sessions = RemoteSessionManager(self.store)
        self.widgets = WidgetEngine(self.store)
        self.web = WebRuntime(self.store)

    def status(self) -> dict:
        return {
            "account": self.identity.account(),
            "devices": len(self.devices.devices()),
            "pairing_requests": len(self.devices.pairing_requests()),
            "sync": self.sync.status(),
            "push_queued": len(self.push.outbox()),
            "offline_queued": len(self.offline.queue()),
            "sessions": len(self.sessions.sessions()),
            "widgets": len(self.widgets.widgets()),
            "web": self.web.status(),
        }
