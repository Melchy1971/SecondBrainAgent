from __future__ import annotations

import importlib
import inspect
import json
import sqlite3

import pytest

from secondbrain.importing import Attachment, Conversation, Message, Metadata, Source, StreamingImportService


CASES = {
    "chatgpt": {"id": "cg", "title": "ChatGPT", "mapping": {"m": {"message": {"id": "m1", "author": {"role": "user"}, "content": {"parts": ["hello"]}, "attachments": [{"id": "a1", "name": "one.txt"}]}}}},
    "openai_export": {"id": "oa", "title": "OpenAI", "mapping": {"m": {"message": {"author": {"role": "assistant"}, "content": {"parts": ["answer"]}}}}},
    "claude": {"uuid": "cl", "name": "Claude", "chat_messages": [{"uuid": "m1", "sender": "human", "text": "hello", "files": [{"file_name": "note.txt", "url": "file://note"}]}]},
    "gemini": {"id": "ge", "title": "Gemini", "messages": [{"role": "user", "content": "prompt", "attachments": [{"name": "image.png", "mime_type": "image/png"}]}]},
    "perplexity": {"id": "px", "query": "Question", "answer": "Answer", "sources": ["https://example.test/source"]},
    "librechat": {"conversationId": "lc", "title": "LibreChat", "messages": [{"message_id": "m1", "sender": "User", "text": "hello"}]},
    "anythingllm": {"id": "al", "title": "AnythingLLM", "chats": [{"id": "c1", "prompt": "question", "response": "answer"}]},
    "openwebui": {"id": "ow", "chat": {"title": "OpenWebUI", "history": {"messages": {"m1": {"id": "m1", "role": "user", "content": "hello"}}}}},
}


@pytest.mark.parametrize("provider", CASES)
def test_all_provider_formats_normalize_to_canonical_model(provider, tmp_path):
    conversation = StreamingImportService.normalize(CASES[provider], provider, tmp_path / "export.json")
    assert isinstance(conversation, Conversation)
    assert isinstance(conversation.source, Source)
    assert isinstance(conversation.metadata, Metadata)
    assert conversation.source.provider == provider
    assert conversation.messages and all(isinstance(message, Message) for message in conversation.messages)
    assert all(isinstance(attachment, Attachment) for attachment in conversation.attachments)


@pytest.mark.parametrize("provider", CASES)
def test_all_provider_formats_use_streaming_import_and_canonical_metadata(provider, tmp_path):
    source = tmp_path / f"{provider}.json"
    source.write_text(json.dumps([CASES[provider]]), encoding="utf-8")
    service = StreamingImportService(tmp_path, batch_size=1)
    session = service.import_file(source, source=provider)
    with sqlite3.connect(service.db_path) as connection:
        metadata = json.loads(connection.execute("SELECT metadata_json FROM documents").fetchone()[0])
    assert session.imported_chats == 1
    assert metadata["schema"] == "secondbrain.conversation.v1"
    assert metadata["source"]["provider"] == provider
    assert metadata["messages"]


@pytest.mark.parametrize("module_name,function_name", [
    ("modules.chatgpt_importer.importer", "import_chatgpt_zip"),
    ("modules.claude_importer.importer", "import_claude_export"),
    ("modules.gemini_importer.importer", "import_gemini_export"),
    ("modules.perplexity_importer.importer", "import_perplexity_export"),
    ("modules.librechat_importer.importer", "import_librechat_export"),
    ("modules.anythingllm_importer.importer", "import_anythingllm_export"),
    ("modules.openwebui_importer.importer", "import_openwebui_export"),
    ("modules.openai_export_importer.importer", "import_openai_export"),
])
def test_importer_entrypoints_delegate_exclusively_to_streaming_service(module_name, function_name):
    function = getattr(importlib.import_module(module_name), function_name)
    source = inspect.getsource(function)
    assert "StreamingImportService" in source
    assert "json.load" not in source
    assert "read_text" not in source
    assert "ZipFile" not in source
