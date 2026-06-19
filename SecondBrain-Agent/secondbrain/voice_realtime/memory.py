from __future__ import annotations
from .json_store import JsonStore

class VoiceMemory:
    def __init__(self, store: JsonStore): self.store = store
    def remember(self, event: dict): return self.store.append('voice_memory', event, limit=1000)
    def recent(self, limit: int = 20): return self.store.read('voice_memory', [])[-limit:]
    def status(self): return {'items': len(self.store.read('voice_memory', []))}
