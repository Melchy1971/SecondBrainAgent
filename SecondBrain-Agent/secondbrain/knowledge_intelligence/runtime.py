from uuid import uuid4
from .store import KnowledgeStore
from .entities import EntityExtractor, EntityResolver
from .relationships import RelationshipDiscovery
from .timeline import TimelineAnalytics
from .clustering import SemanticClustering
from .contradictions import ContradictionDetector


class KnowledgeIntelligence:
    def __init__(self, root="."):
        self.store = KnowledgeStore(root)
        self.extractor = EntityExtractor()
        self.resolver = EntityResolver(self.store)
        self.relationships = RelationshipDiscovery(self.store)
        self.timeline = TimelineAnalytics(self.store)
        self.clustering = SemanticClustering(self.store)
        self.contradictions = ContradictionDetector(self.store)

    def status(self) -> dict:
        return {
            "entities": len(self.resolver.entities()),
            "relationships": len(self.relationships.relationships()),
            "timeline_events": len(self.timeline.timeline()),
            "claims": len(self.store.load("claims", [])),
            "backend": "json_graph_neo4j_ready",
        }

    def ingest_text(self, text: str, source: str = "manual") -> dict:
        doc_id = str(uuid4())
        entities = self.resolver.resolve(self.extractor.extract(text))
        relationships = self.relationships.discover(doc_id, entities)
        claims = self.contradictions.scan_claims(text, source)
        for entity in entities:
            self.timeline.add_event(f"Entity mentioned: {entity['name']}", "mention", entity["name"])
        return {
            "doc_id": doc_id,
            "entities": entities,
            "relationships": relationships,
            "claims": claims,
        }

    def graph_export(self) -> dict:
        return {
            "nodes": self.resolver.entities(),
            "edges": self.relationships.relationships(),
        }
