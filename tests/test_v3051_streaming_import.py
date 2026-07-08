from __future__ import annotations

import inspect
import json
import sqlite3
import tracemalloc
import zipfile
from pathlib import Path

from secondbrain.importing import StreamingImportService
from secondbrain.native.ai_workspace.service import AIWorkspaceService


def _rows(path: Path, count: int, *, size: int = 20) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for index in range(count):
            handle.write(json.dumps({"title": f"Chat {index}", "content": "x" * size}) + "\n")


def _counts(service: StreamingImportService) -> tuple[int, int]:
    with sqlite3.connect(service.db_path) as connection:
        return connection.execute("select count(*) from documents").fetchone()[0], connection.execute("select count(*) from chunks").fetchone()[0]


def _drain(service: StreamingImportService) -> None:
    service.scheduler.pool.run_until_idle(timeout=10)


def test_streaming_json_array_batches_into_existing_rag_store(tmp_path):
    source = tmp_path / "chatgpt.json"
    source.write_text(json.dumps([{"title": f"C{i}", "content": f"Nachricht {i}"} for i in range(7)]), encoding="utf-8")
    service = StreamingImportService(tmp_path, batch_size=3)
    session = service.import_file(source, source="chatgpt")
    assert session.status == "completed"
    assert session.imported_chats == 7
    assert session.position == 7
    assert session.bytes_processed == source.stat().st_size
    _drain(service)
    assert _counts(service) == (7, 7)
    assert service.queue.snapshot()["counts"]["success"] >= 1


def test_resume_uses_checkpoint_without_duplicate_documents(tmp_path):
    source = tmp_path / "claude.jsonl"
    _rows(source, 5)
    service = StreamingImportService(tmp_path, batch_size=2)
    paused = service.import_file(source, source="claude", stop_after_batches=1)
    assert paused.status == "paused"
    assert paused.position == 2
    assert paused.imported_chats == 2
    resumed = service.resume(paused.session_id)
    assert resumed.status == "completed"
    assert resumed.imported_chats == 5
    assert _counts(service)[0] == 5
    stored = service.checkpoints.get(paused.session_id)
    assert stored is not None and stored.position == 5 and stored.error == ""


def test_checkpoint_schema_contains_enterprise_counters(tmp_path):
    source = tmp_path / "data.jsonl"; _rows(source, 1)
    service = StreamingImportService(tmp_path)
    session = service.import_file(source, source="jsonl")
    with sqlite3.connect(service.db_path) as connection:
        columns = {row[1] for row in connection.execute("pragma table_info(import_sessions)")}
        row = connection.execute("select bytes_processed,position,imported_chats,chunks,embeddings,status,error from import_sessions where session_id=?", (session.session_id,)).fetchone()
    assert {"session_id", "file_path", "bytes_processed", "position", "imported_chats", "chunks", "embeddings", "status", "error"}.issubset(columns)
    assert row[:4] == (source.stat().st_size, 1, 1, 0)
    assert row[4:] == (0, "completed", "")


def test_large_file_simulation_has_bounded_python_memory(tmp_path):
    source = tmp_path / "large.jsonl"
    _rows(source, 1000, size=8192)
    service = StreamingImportService(tmp_path, batch_size=20)
    tracemalloc.start()
    session = service.import_file(source, source="jsonl")
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert source.stat().st_size > 8_000_000
    assert peak < source.stat().st_size
    assert session.imported_chats == 1000


def test_markdown_and_zip_are_streamed(tmp_path):
    markdown = tmp_path / "large.md"
    markdown.write_text("# Titel\n" + ("Absatz\n" * 30_000), encoding="utf-8")
    service = StreamingImportService(tmp_path, batch_size=2)
    md_session = service.import_file(markdown, source="markdown")
    assert md_session.imported_chats > 1
    archive = tmp_path / "gemini.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("conversations.json", json.dumps([{"title": "Gemini", "content": "Hallo"}]))
    zip_session = service.import_file(archive, source="gemini")
    assert zip_session.imported_chats == 1


def test_engine_uses_ijson_and_contains_no_full_json_load():
    import secondbrain.importing.streaming as streaming
    source = inspect.getsource(streaming)
    assert "ijson.items" in source
    assert "json.load(" not in source
    assert "read_text(" not in inspect.getsource(StreamingImportService._stream)


def test_provider_adapters_delegate_without_full_json_reads():
    import modules.chatgpt_importer.importer as chatgpt
    import modules.gemini_importer.importer as gemini
    assert "StreamingImportService" in inspect.getsource(chatgpt.import_chatgpt_zip)
    assert "StreamingImportService" in inspect.getsource(gemini.import_gemini_export)
    assert "read_text(" not in inspect.getsource(chatgpt.import_chatgpt_zip)
    assert "read_text(" not in inspect.getsource(gemini.import_gemini_export)


def test_chatgpt_mapping_is_streamed_and_secrets_are_redacted(tmp_path):
    secret = "sk-proj-" + ("abc123_" * 8)
    payload = [{"id": "c1", "title": "Secret", "mapping": {"m1": {"message": {
        "author": {"role": "user"}, "content": {"parts": [f"Token {secret}"]}, "create_time": 1}}}}]
    source = tmp_path / "chatgpt-export.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    service = StreamingImportService(tmp_path)
    session = service.import_file(source, source="chatgpt")
    _drain(service)
    with sqlite3.connect(service.db_path) as connection:
        content = connection.execute("select text from chunks limit 1").fetchone()[0]
    assert session.imported_chats == 1
    assert secret not in content
    assert "[REDACTED_OPENAI_API_KEY]" in content


def test_nested_provider_array_is_streamed(tmp_path):
    source = tmp_path / "gemini.json"
    source.write_text(json.dumps({"conversations": [{"title": "A", "content": "eins"}, {"title": "B", "content": "zwei"}]}), encoding="utf-8")
    session = StreamingImportService(tmp_path, batch_size=1).import_file(source, source="gemini")
    assert session.imported_chats == 2


def test_ai_workspace_exposes_real_import_center(tmp_path):
    workspace = AIWorkspaceService(tmp_path)
    modules = {module.id: module for module in workspace.snapshot().modules}
    assert "imports" in modules
    assert modules["imports"].status == "missing"
    assert AIWorkspaceService.VERSION == "v30.57"
