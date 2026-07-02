from pathlib import Path

from secondbrain.native.chat import ChatContextBuilder


class FakeRag:
    def hybrid_search(self, query: str, limit: int = 5):
        return {"ok": True, "hits": [{"document_id": "doc-1", "chunk_id": "c-1", "title": "Plan", "source": "plan.md", "text": "Hybrid Kontext", "score": 0.8}]}


class FakeMemory:
    def search(self, query: str, limit: int = 5):
        return {"ok": True, "memories": [{"content": "Semantische Erinnerung"}]}


def test_context_builder_combines_existing_memory_and_hybrid_search(tmp_path: Path) -> None:
    builder = ChatContextBuilder(tmp_path, rag_runtime=FakeRag(), memory_explorer=FakeMemory())
    payload = builder.build("Status", [{"role": "user", "content": "Vorher"}], selected_documents=["doc-1"])
    assert "Conversation Memory" in payload["context"]
    assert "Semantische Erinnerung" in payload["context"]
    assert "Hybrid Kontext" in payload["context"]
    assert payload["citations"][0]["chunk"] == "c-1"


def test_context_builder_honors_selected_documents(tmp_path: Path) -> None:
    builder = ChatContextBuilder(tmp_path, rag_runtime=FakeRag(), memory_explorer=FakeMemory())
    payload = builder.build("Status", [], selected_sources=["documents"], selected_documents=["other"])
    assert payload["hits"] == []
    assert payload["memories"] == []

