from datetime import datetime, timezone
from uuid import uuid4


class VoiceMemory:
    def __init__(self, store):
        self.store = store

    def remember(self, text: str, kind: str = "utterance") -> dict:
        item = {
            "id": str(uuid4()),
            "text": text,
            "kind": kind,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.store.append("voice_memory", item)

    def recall(self, query: str) -> list[dict]:
        q = query.lower()
        return [m for m in self.store.load("voice_memory", []) if q in m["text"].lower()]

    def all(self) -> list[dict]:
        return self.store.load("voice_memory", [])
