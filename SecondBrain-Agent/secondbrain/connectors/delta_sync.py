"""P4 v22.1 - Delta Synchronisation."""

from dataclasses import dataclass
from time import time


@dataclass
class SyncCheckpoint:
    connector: str
    cursor: str | None
    updated_at: float = time()


class DeltaSynchronizer:
    def __init__(self):
        self._checkpoints: dict[str, SyncCheckpoint] = {}

    def save_checkpoint(self, connector: str, cursor: str | None):
        self._checkpoints[connector] = SyncCheckpoint(connector, cursor)

    def get_checkpoint(self, connector: str):
        return self._checkpoints.get(connector)
