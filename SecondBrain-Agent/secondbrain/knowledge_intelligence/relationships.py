from uuid import uuid4


class RelationshipDiscovery:
    def __init__(self, store):
        self.store = store

    def discover(self, doc_id: str, entities: list[dict]) -> list[dict]:
        relationships = []
        for i, source in enumerate(entities):
            for target in entities[i + 1:]:
                relationships.append({
                    "id": str(uuid4()),
                    "source": source["name"],
                    "target": target["name"],
                    "type": "co_occurs_with",
                    "weight": 0.5,
                    "doc_id": doc_id,
                })
        existing = self.store.load("relationships", [])
        existing.extend(relationships)
        self.store.save("relationships", existing)
        return relationships

    def relationships(self) -> list[dict]:
        return self.store.load("relationships", [])

    def neighbors(self, entity: str) -> list[dict]:
        e = entity.lower()
        return [
            r for r in self.relationships()
            if r["source"].lower() == e or r["target"].lower() == e
        ]
