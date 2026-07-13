from secondbrain.knowledge_graph import KnowledgeGraphRuntime


def test_status(tmp_path):
    kg = KnowledgeGraphRuntime(tmp_path)
    assert kg.status()["backend"] == "sqlite_graph_neo4j_ready"


def test_nodes_edges_neighbors(tmp_path):
    kg = KnowledgeGraphRuntime(tmp_path)
    kg.add_edge("Jarvis", "SecondBrain", "powers")
    assert kg.nodes("jarvis")
    assert kg.edges()
    assert kg.neighbors("Jarvis")


def test_shortest_path(tmp_path):
    kg = KnowledgeGraphRuntime(tmp_path)
    kg.add_edge("A", "B")
    kg.add_edge("B", "C")
    path = kg.shortest_path("A", "C")
    assert path["ok"] is True


def test_communities(tmp_path):
    kg = KnowledgeGraphRuntime(tmp_path)
    kg.add_edge("A", "B")
    kg.add_edge("X", "Y")
    communities = kg.communities()
    assert len(communities) == 2


def test_timeline_export(tmp_path):
    kg = KnowledgeGraphRuntime(tmp_path)
    kg.add_node("Jarvis")
    kg.add_event("Release", "release", "Jarvis")
    assert kg.timeline("Jarvis")
    assert kg.export_neo4j_cypher()["count"] >= 1
