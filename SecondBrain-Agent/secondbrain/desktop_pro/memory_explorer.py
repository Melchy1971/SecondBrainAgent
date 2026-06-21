class MemoryExplorer:
    def __init__(self, store):
        self.store = store

    def add_memory(self, text: str, source: str = "manual") -> dict:
        memory = {"id": f"mem_{len(self.memories())+1}", "text": text, "source": source}
        return self.store.append("memories", memory)

    def memories(self) -> list[dict]:
        return self.store.load("memories", [])

    def search(self, query: str) -> list[dict]:
        q = query.lower()
        return [m for m in self.memories() if q in m["text"].lower() or q in m.get("source", "").lower()]
