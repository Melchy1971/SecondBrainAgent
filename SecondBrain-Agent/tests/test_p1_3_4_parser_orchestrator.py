from __future__ import annotations

from pathlib import Path

from secondbrain.document_understanding.orchestrator import (
    MultiFormatParserOrchestrator,
    default_multi_format_orchestrator,
)
from secondbrain.document_understanding.parser_contract import ParseStatus, build_parsed_document


class ExplodingParser:
    supported_extensions = {".boom"}

    def parse(self, path: str | Path):
        raise RuntimeError("boom")


class MimeOnlyTextParser:
    supported_extensions = {".custom"}

    def parse(self, path: str | Path):
        return build_parsed_document(
            title="custom",
            text="custom mime text with enough characters",
            mime_type="application/x-custom",
            source_path=path,
        )


def test_default_orchestrator_parses_text_by_extension(tmp_path: Path) -> None:
    path = tmp_path / "note.txt"
    path.write_text("Hello from parser orchestration", encoding="utf-8")

    result = default_multi_format_orchestrator().parse(path)

    assert result.ok is True
    assert result.parsed.status == ParseStatus.PARSED
    assert result.selection.reason == "extension"
    assert result.selection.parser_name == "PlainTextParser"
    assert result.to_dict()["chars"] > 0


def test_orchestrator_prefers_explicit_mime_type(tmp_path: Path) -> None:
    path = tmp_path / "payload.bin"
    path.write_text("ignored suffix but accepted by mime", encoding="utf-8")
    orchestrator = MultiFormatParserOrchestrator()
    orchestrator.register(MimeOnlyTextParser(), name="MimeOnly", mime_types=("application/x-custom",))

    result = orchestrator.parse(path, mime_type="application/x-custom")

    assert result.ok is True
    assert result.selection.reason == "mime_type"
    assert result.selection.parser_name == "MimeOnly"


def test_orchestrator_returns_unsupported_without_crash(tmp_path: Path) -> None:
    path = tmp_path / "archive.xyz"
    path.write_text("not supported", encoding="utf-8")

    result = default_multi_format_orchestrator().parse(path)

    assert result.ok is False
    assert result.parsed.status == ParseStatus.UNSUPPORTED
    assert result.selection.reason == "unsupported"
    assert result.to_dict()["errors"] == ["unsupported_file_type"]


def test_orchestrator_converts_parser_exception_to_failed_result(tmp_path: Path) -> None:
    path = tmp_path / "bad.boom"
    path.write_text("bad", encoding="utf-8")
    orchestrator = MultiFormatParserOrchestrator()
    orchestrator.register(ExplodingParser(), name="Exploding")

    result = orchestrator.parse(path)

    assert result.ok is False
    assert result.parsed.status == ParseStatus.FAILED
    assert result.selection.parser_name == "Exploding"
    assert result.parsed.errors[0].startswith("parser_exception:")


def test_orchestrator_marks_very_short_text_warning(tmp_path: Path) -> None:
    path = tmp_path / "short.txt"
    path.write_text("tiny", encoding="utf-8")

    result = default_multi_format_orchestrator().parse(path)

    assert result.parsed.status == ParseStatus.PARSED
    assert "very_short_text" in result.warnings
