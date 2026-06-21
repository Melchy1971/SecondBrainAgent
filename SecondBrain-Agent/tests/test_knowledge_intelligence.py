from secondbrain.knowledge_intelligence import KnowledgeIntelligence


def test_status_empty(tmp_path):
    ki = KnowledgeIntelligence(tmp_path)
    assert ki.status()["backend"] == "json_graph_neo4j_ready"


def test_ingest_entities_relationships(tmp_path):
    ki = KnowledgeIntelligence(tmp_path)
    result = ki.ingest_text("Jarvis nutzt Gmail und GitHub für SecondBrain.")
    assert len(result["entities"]) >= 3
    assert ki.status()["relationships"] >= 1


def test_neighbors_and_export(tmp_path):
    ki = KnowledgeIntelligence(tmp_path)
    ki.ingest_text("Jarvis verbindet Gmail und GitHub.")
    assert ki.relationships.neighbors("Jarvis")
    assert "nodes" in ki.graph_export()


def test_clusters(tmp_path):
    ki = KnowledgeIntelligence(tmp_path)
    ki.ingest_text("Jarvis nutzt Neo4j.")
    clusters = ki.clustering.cluster_entities()
    assert clusters


def test_contradictions(tmp_path):
    ki = KnowledgeIntelligence(tmp_path)
    ki.contradictions.scan_claims("Jarvis ist aktiv")
    ki.contradictions.scan_claims("Jarvis ist nicht aktiv")
    assert ki.contradictions.contradictions()
