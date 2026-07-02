from pathlib import Path

from secondbrain.native.chat import NativeChatService
from secondbrain.providers.base.provider_models import CompletionResponse, StreamChunk


class FakeProviderManager:
    def complete(self, provider: str, request):
        assert request.messages[-1].content == "Was ist neu?"
        return CompletionResponse(provider=provider, model=request.model, content="Antwort [1]")

    def stream(self, provider: str, request):
        yield StreamChunk(provider=provider, model=request.model, delta="Ant")
        yield StreamChunk(provider=provider, model=request.model, delta="wort", done=True)


class FakeRag:
    def hybrid_search(self, query: str, limit: int = 5):
        return {"ok": True, "hits": [{"document_id": "doc", "chunk_id": "chunk", "title": "Quelle", "source": "source.md", "text": "Evidenz", "score": 0.9}]}


class FakeMemory:
    def search(self, query: str, limit: int = 5):
        return {"ok": True, "memories": [{"content": "Memory"}]}


def test_chat_service_runs_pipeline_and_persists_citations(tmp_path: Path) -> None:
    service = NativeChatService(tmp_path, provider_manager=FakeProviderManager(), rag_runtime=FakeRag(), memory_explorer=FakeMemory())
    result = service.send("Was ist neu?", provider="ollama", model="test")
    assert result["ok"] is True
    assert result["answer"] == "Antwort [1]"
    assert result["citations"][0]["document_id"] == "doc"
    messages = service.conversations.messages(result["conversation"]["id"])
    assert [message["role"] for message in messages] == ["user", "assistant"]


def test_chat_service_stream_and_provider_version(tmp_path: Path) -> None:
    service = NativeChatService(tmp_path, provider_manager=FakeProviderManager(), rag_runtime=FakeRag(), memory_explorer=FakeMemory())
    first = service.send("Was ist neu?", provider="ollama", model="a")
    chunks = list(service.stream_response("Weiter", conversation_id=first["conversation"]["id"], provider="openai", model="b"))
    assert "".join(chunk.delta for chunk in chunks) == "Antwort"
    version = service.conversations.get(service.last_conversation_id)
    assert version["parent_id"] == first["conversation"]["id"]


def test_chat_service_splits_provider_fallback_chunk_into_ui_tokens(tmp_path: Path) -> None:
    service = NativeChatService(tmp_path, provider_manager=FakeProviderManager(), rag_runtime=FakeRag(), memory_explorer=FakeMemory())
    chunks = service._token_chunks(StreamChunk(provider="ollama", model="test", delta="Token fuer Token", done=True))
    assert [chunk.delta for chunk in chunks] == ["Token ", "fuer ", "Token"]
    assert chunks[-1].done is True
