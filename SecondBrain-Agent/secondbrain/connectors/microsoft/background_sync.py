"""M365 background sync (thin wrapper over the shared scaffold BackgroundSync)."""
from secondbrain.connectors.scaffold.sync import BackgroundSync


class M365BackgroundSync(BackgroundSync):
    pass


__all__ = ["M365BackgroundSync"]
