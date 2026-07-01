from pathlib import Path

from secondbrain.native.actions import NativeActionDispatcher
from secondbrain.native.runtime_snapshot import build_native_view_model
from secondbrain.native.voice_de import GermanVoiceCommandParser


def test_native_view_model_exposes_action_bridge(tmp_path: Path):
    model = build_native_view_model(tmp_path)
    assert model["schema"] == "secondbrain.native.view_model.v30_27"
    assert model["version"] == "30.27"
    assert model["voice"]["action_dispatcher"] is True
    assert "actions" in model
    assert "p1-vector-index-repair" in model["actions"]["confirmation_required_for"]


def test_voice_open_dispatch_navigates_without_subprocess(tmp_path: Path):
    dispatcher = NativeActionDispatcher(tmp_path)
    result = dispatcher.parse_and_dispatch("Öffne Dokumente")
    assert result.ok is True
    assert result.status == "navigated"
    assert result.executed is False
    assert result.next_view == "documents"


def test_mutating_voice_action_requires_confirmation(tmp_path: Path):
    dispatcher = NativeActionDispatcher(tmp_path)
    result = dispatcher.parse_and_dispatch("Repariere Index")
    assert result.ok is False
    assert result.status == "confirmation_required"
    assert result.requires_confirmation is True
    assert result.command == "p1-vector-index-repair"


def test_memory_note_is_written_when_confirmed(tmp_path: Path):
    dispatcher = NativeActionDispatcher(tmp_path)
    result = dispatcher.parse_and_dispatch("Merke Testnotiz", confirmed=True)
    assert result.ok is True
    assert result.status == "executed"
    note_file = tmp_path / "runtime" / "native" / "voice_notes.jsonl"
    assert note_file.exists()
    assert "Testnotiz" in note_file.read_text(encoding="utf-8")


def test_parser_keeps_german_command_surface():
    parser = GermanVoiceCommandParser()
    assert parser.parse("Jarvis Status").command == "native-status"
    assert parser.parse("Suche Rechnung Telekom").command == "p1-rag-hybrid-search"
    assert parser.parse("Frage was fehlt noch").command == "p1-rag-answer"
