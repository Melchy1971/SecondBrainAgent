from secondbrain.memory.semantic_memory import SemanticMemoryItem, SemanticMemoryStore
from secondbrain.memory.episodic_memory import EpisodicMemory, EpisodicMemoryStore


def test_semantic_memory_store():
    store = SemanticMemoryStore()
    store.upsert(SemanticMemoryItem("1", "hello"))
    assert store.get("1").text == "hello"


def test_episodic_memory_store():
    store = EpisodicMemoryStore()
    store.add(EpisodicMemory("1", "created project"))
    assert len(store.list()) == 1
