
from secondbrain.knowledge_graph_v123 import KnowledgeGraphEngine
from secondbrain.launcher_runtime_v123 import SecondBrainLauncherV123

def test_graph_ingest_and_search(tmp_path):
    g=KnowledgeGraphEngine(tmp_path)
    out=g.ingest_text('Jarvis nutzt Gmail am 2026-06-19. Markus verwendet Jarvis.', 'demo')
    assert out['entities'] >= 3
    assert g.search_entities('Jarvis')
    assert g.graph_status()['relationships'] >= 1
    assert g.graph_status()['timeline_events'] >= 1

def test_launcher_graph_commands(tmp_path):
    l=SecondBrainLauncherV123(tmp_path)
    res=l.graph_ingest_text('SecondBrain nutzt Neo4j und RAG.', 'unit')
    assert res['entities'] >= 2
    assert l.graph_search('SecondBrain')
    assert l.core123_status()['version']=='12.3'
