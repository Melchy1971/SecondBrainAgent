from pathlib import Path

from secondbrain.desktop_native.status import native_desktop_status
from secondbrain.desktop_native.voice_de import GermanVoiceController, parse_german_voice_command
from secondbrain.gui.launch import GUI_COMMANDS, gui_status, shortcut_manifest


def test_native_commands_are_registered():
    assert {"native-gui", "native-status", "voice-status", "voice-parse", "gui-web", "hud"}.issubset(GUI_COMMANDS)


def test_native_status_is_safe_without_optional_voice_deps(tmp_path: Path):
    (tmp_path / "launcher.py").write_text("", encoding="utf-8")
    payload = native_desktop_status(tmp_path, repair=True)
    assert payload["schema"] == "secondbrain.native_desktop.status.v1"
    assert payload["mode"] == "native_desktop"
    assert payload["web_primary"] is False
    assert payload["voice"]["language"] == "de-DE"


def test_german_voice_parser_core_intents():
    assert parse_german_voice_command("Jarvis Status").intent == "status"
    search = parse_german_voice_command("Suche pgvector migration")
    assert search.intent == "rag_search"
    assert search.args["query"] == "pgvector migration"
    assert parse_german_voice_command("Öffne Dokumente").args["view"] == "documents"
    repair = parse_german_voice_command("Repariere Index")
    assert repair.intent == "vector_repair"
    assert repair.needs_confirmation is True


def test_voice_controller_parse_uses_de_language(tmp_path: Path):
    ctrl = GermanVoiceController(tmp_path)
    status = ctrl.status()
    assert status["language"] == "de-DE"
    parsed = ctrl.parse("Frage was fehlt noch")
    assert parsed["intent"] == "rag_answer"


def test_gui_status_and_shortcuts_mark_native_as_primary(tmp_path: Path):
    (tmp_path / "launcher.py").write_text("", encoding="utf-8")
    payload = gui_status(tmp_path)
    assert payload["mode"] == "native_desktop"
    assert payload["web_primary"] is False
    shortcuts = shortcut_manifest(tmp_path)
    assert any(item["starts"] == "Native Desktop App" for item in shortcuts["desktop_shortcuts"])
    assert "python launcher.py native-gui" in shortcuts["manual_start"]
