class SemanticClustering:
    def __init__(self, store):
        self.store = store

    def cluster_entities(self) -> list[dict]:
        entities = self.store.load("entities", [])
        clusters = {}
        for e in entities:
            kind = e.get("kind", "concept")
            clusters.setdefault(kind, []).append(e["name"])
        result = [{"cluster": kind, "items": sorted(items), "size": len(items)} for kind, items in clusters.items()]
        self.store.save("clusters", result)
        return result
