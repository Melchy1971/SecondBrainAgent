class KnowledgeExplorer:
    def __init__(self, store):
        self.store = store

    def ingest_node(self, title: str, kind: str = "note", tags: list[str] | None = None) -> dict:
        node = {"id": f"node_{len(self.nodes())+1}", "title": title, "kind": kind, "tags": tags or []}
        return self.store.append("knowledge_nodes", node)

    def nodes(self) -> list[dict]:
        return self.store.load("knowledge_nodes", [])

    def search(self, query: str) -> list[dict]:
        q = query.lower()
        return [n for n in self.nodes() if q in n["title"].lower() or any(q in t.lower() for t in n.get("tags", []))]
