from __future__ import annotations

from pathlib import Path

from launcher import main
from secondbrain.module_registry import ModuleRegistry
from secondbrain.p1_rag_runtime import P1RagRuntime


def test_ingest_file_failure_includes_structured_parse_event(tmp_path: Path):
    bad = tmp_path / "broken.json"
    bad.write_text('{"broken": ', encoding="utf-8")

    result = P1RagRuntime(tmp_path).ingest_file(bad)

    assert result["ok"] is False
    assert result["error"] == "parse_failed"
    assert result["parse"]["schema"] == "secondbrain.p1_parse_event.v1"
    assert result["parse"]["status"] == "failed"
    assert result["parse"]["mime_type"] == "application/json"
    assert result["metadata"]["parse_status"] == "failed"
    assert result["metadata"]["parse_errors"]


def test_ingest_file_success_includes_full_parse_event(tmp_path: Path):
    note = tmp_path / "note.md"
    note.write_text("# Titel\n\nRAG Parser Registry Success.", encoding="utf-8")

    result = P1RagRuntime(tmp_path).ingest_file(note)

    assert result["ok"] is True
    assert result["parse"]["schema"] == "secondbrain.p1_parse_event.v1"
    assert result["parse"]["status"] == "parsed"
    assert result["parse"]["chars"] > 0
    assert result["parse"]["requires_ocr"] is False
    assert result["metadata"]["ingest_mode"] == "parser_registry"


def test_ingest_directory_reports_mixed_results(tmp_path: Path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "a.txt").write_text("Jarvis Alpha", encoding="utf-8")
    (inbox / "b.md").write_text("Jarvis Beta", encoding="utf-8")
    (inbox / "bad.json").write_text('{"broken": ', encoding="utf-8")

    result = P1RagRuntime(tmp_path).ingest_directory(inbox)

    assert result["schema"] == "secondbrain.p1_rag.directory_ingest.v1"
    assert result["ok"] is False
    assert result["files"] == 3
    assert result["ingested"] == 2
    assert result["blocked"] == 1
    assert result["counts"]["parse_failed"] == 1


def test_launcher_ingest_dir_command(tmp_path: Path, capsys):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "a.txt").write_text("Jarvis CLI Directory Import", encoding="utf-8")

    rc = main(["--project-root", str(tmp_path), "p1-rag-ingest-dir", str(inbox)])
    captured = capsys.readouterr().out

    assert rc == 0
    assert "directory_ingest" in captured
    assert '"ingested": 1' in captured


def test_command_index_contains_ingest_dir():
    assert ModuleRegistry().command_index()["p1-rag-ingest-dir"] == "core"
