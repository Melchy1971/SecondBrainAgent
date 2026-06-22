from secondbrain.memory.memory_graph import MemoryGraph
from secondbrain.memory.entity_extractor import EntityExtractor
from secondbrain.memory.memory_deduplicator import MemoryDeduplicator
from secondbrain.memory.memory_decay import MemoryDecay
from secondbrain.gates.p3_production_gate import P3ProductionGate


def test_memory_graph():
    graph = MemoryGraph()
    graph.connect("a", "b")
    assert graph.neighbors("a") == ["b"]


def test_entity_extraction():
    entities = EntityExtractor().extract("Markus arbeitet bei Deutsche Telekom")
    assert "Markus" in entities


def test_deduplication():
    result = MemoryDeduplicator().deduplicate(["Hallo", "hallo", "Welt"])
    assert len(result) == 2


def test_decay():
    assert MemoryDecay().score(0) >= 0


def test_p3_gate():
    caps = {k: True for k in P3ProductionGate.REQUIRED}
    assert P3ProductionGate().evaluate(caps)["status"] == "PASS"
