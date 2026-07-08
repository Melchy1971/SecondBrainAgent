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


# --- v30.46.1: ChatService-Fassade (eine API fuer alle Oberflaechen) ---------


def _facade(tmp_path: Path):
    from secondbrain.chat import ChatService

    return ChatService(tmp_path, provider_manager=FakeProviderManager(), rag_runtime=FakeRag(), memory_explorer=FakeMemory())


def test_facade_ask_delegates_to_engine(tmp_path: Path) -> None:
    chat = _facade(tmp_path)
    result = chat.ask("Was ist neu?", provider="ollama", model="test")
    assert result["ok"] is True
    assert result["answer"] == "Antwort [1]"
    assert chat.last_conversation_id == result["conversation"]["id"]


def test_facade_stream_blocking_iterator(tmp_path: Path) -> None:
    chat = _facade(tmp_path)
    chunks = list(chat.stream("Was ist neu?", provider="ollama", model="test"))
    assert "".join(chunk.delta for chunk in chunks) == "Antwort"


def test_facade_stream_with_callbacks_and_cancel(tmp_path: Path) -> None:
    chat = _facade(tmp_path)
    done: list[str] = []
    manager = chat.stream(
        "Was ist neu?",
        provider="ollama",
        model="test",
        on_done=lambda content, cancelled: done.append(content),
    )
    assert manager.wait(5)
    assert done == ["Antwort"]
    assert chat.cancel() is True  # idle: setzt Cancel-Event defensiv


def test_facade_retry_repeats_last_question(tmp_path: Path) -> None:
    chat = _facade(tmp_path)
    first = chat.ask("Was ist neu?", provider="ollama", model="test")
    again = chat.retry()
    assert again["ok"] is True
    assert again["conversation"]["id"] == first["conversation"]["id"]
    assert chat.retry(provider="ollama", model="test")["ok"] is True


def test_facade_retry_without_history(tmp_path: Path) -> None:
    chat = _facade(tmp_path)
    assert chat.retry() == {"ok": False, "status": "nothing_to_retry"}


def test_facade_export_and_import_roundtrip(tmp_path: Path) -> None:
    chat = _facade(tmp_path)
    result = chat.ask("Was ist neu?", provider="ollama", model="test")
    exported = chat.export(format="json")
    assert exported["ok"] is True
    imported = chat.import_(exported["path"])
    assert imported["ok"] is True
    assert imported["messages"] == 2
    new_id = imported["conversation"]["id"]
    assert new_id != result["conversation"]["id"]
    contents = [row["content"] for row in chat.conversations.messages(new_id)]
    assert contents == ["Was ist neu?", "Antwort [1]"]


def test_facade_state_reflects_conversation(tmp_path: Path) -> None:
    chat = _facade(tmp_path)
    chat.ask("Was ist neu?", provider="ollama", model="test")
    state = chat.state()
    assert state.conversation_id == chat.last_conversation_id
    assert state.message_count == 2
    assert state.status == "idle"
    assert state.citations and state.citations[0]["document_id"] == "doc"
