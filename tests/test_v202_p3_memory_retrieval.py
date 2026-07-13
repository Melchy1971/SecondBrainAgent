from secondbrain.memory.memory_importance import MemoryImportanceScorer
from secondbrain.memory.memory_summarization import MemorySummarizer
from secondbrain.memory.context_window_manager import ContextWindowManager
from secondbrain.memory.persistent_memory_repository import PersistentMemoryRepository


def test_importance_score():
    score = MemoryImportanceScorer().score("test text", access_count=5)
    assert score > 0


def test_summarizer():
    summary = MemorySummarizer().summarize(["a", "b", "c"])
    assert "a" in summary


def test_context_window():
    manager = ContextWindowManager()
    assert manager.trim(["a" * 100, "b" * 100], max_chars=150) == ["a" * 100]


def test_repository(tmp_path):
    repo = PersistentMemoryRepository(str(tmp_path / "memory.json"))
    repo.save({"hello": "world"})
    assert repo.load()["hello"] == "world"
