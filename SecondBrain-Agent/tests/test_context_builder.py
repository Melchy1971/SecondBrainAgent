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


# --- v30.46.2: die eine Context Pipeline (secondbrain.chat.context) ----------


class FakeAttachments:
    def list(self, conversation_id: str):
        return [{"name": "plan.pdf", "extension": ".pdf", "size": 123}]


def test_pipeline_combines_all_stages(tmp_path: Path) -> None:
    from secondbrain.chat.context import ContextBuilder

    builder = ContextBuilder(
        tmp_path,
        rag_runtime=FakeRag(),
        memory_explorer=FakeMemory(),
        attachments=FakeAttachments(),
        agent_context=lambda query, limit: [f"Agent zu {query}"],
        workspace_context=lambda query, limit: ["Workspace aktiv"],
    )
    result = builder.build(
        "Frage",
        [{"role": "user", "content": "Hallo"}],
        selected_sources=("documents", "memory"),
        conversation_id="conv-1",
    )
    context = result["context"]
    assert "Conversation Memory:" in context
    assert "Semantische Erinnerung" in context
    assert "Hybrid Kontext" in context
    assert "plan.pdf" in context
    assert "Agent zu Frage" in context
    assert "Workspace aktiv" in context
    assert result["citations"][0]["document_id"] == "doc-1"
    assert result["budget"]["input_budget"] > 0


def test_pipeline_section_order_matches_briefing(tmp_path: Path) -> None:
    from secondbrain.chat.context import ContextBuilder

    builder = ContextBuilder(
        tmp_path,
        rag_runtime=FakeRag(),
        memory_explorer=FakeMemory(),
        attachments=FakeAttachments(),
    )
    context = builder.build(
        "Frage",
        [{"role": "user", "content": "Hallo"}],
        conversation_id="conv-1",
    )["context"]
    positions = [
        context.index("Conversation Memory:"),
        context.index("Semantic/Working Memory:"),
        context.index("Document Retrieval / Hybrid Search:"),
        context.index("Anhaenge:"),
    ]
    assert positions == sorted(positions)


def test_pipeline_without_document_sources_skips_retrieval(tmp_path: Path) -> None:
    from secondbrain.chat.context import ContextBuilder

    builder = ContextBuilder(tmp_path, rag_runtime=FakeRag(), memory_explorer=FakeMemory())
    result = builder.build("Frage", [], selected_sources=("memory",))
    assert result["hits"] == []
    assert result["citations"] == []


def test_pipeline_budget_limits_oversized_documents(tmp_path: Path) -> None:
    from secondbrain.chat.context import ContextBuilder
    from secondbrain.chat.context.token_budget import TokenBudgetManager

    class HugeRag:
        def hybrid_search(self, query: str, limit: int = 5):
            return {"ok": True, "hits": [{"document_id": "big", "chunk_id": "c", "title": "Big", "source": "big.md", "text": "x" * 50_000, "score": 1.0}]}

    builder = ContextBuilder(
        tmp_path,
        rag_runtime=HugeRag(),
        memory_explorer=FakeMemory(),
        budget=TokenBudgetManager(max_tokens=1024, reserved_output_tokens=0),
    )
    result = builder.build("Frage", [], selected_sources=("documents",))
    assert len(result["context"]) < 50_000
    assert result["budget"]["sections"]["documents"]["over_budget"] is True

