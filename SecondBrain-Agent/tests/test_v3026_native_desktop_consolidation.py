from __future__ import annotations

from pathlib import Path

from secondbrain.gui.launch import GUI_COMMANDS, shortcut_manifest, start_native_gui
from secondbrain.native.runtime_snapshot import build_native_view_model
from secondbrain.native.voice_de import GermanVoiceCommandParser


def test_native_gui_is_primary_start_mode(tmp_path: Path):
    (tmp_path / "launcher.py").write_text("", encoding="utf-8")
    payload = start_native_gui(tmp_path, dry_run=True)
    assert payload["action"] == "native_desktop_primary"
    assert payload["native"]["web_hud"] == "secondary_only"


def test_gui_command_surface_contains_native_and_web_secondary_aliases():
    assert "native-gui" in GUI_COMMANDS
    assert "jarvis" in GUI_COMMANDS
    assert "hud" in GUI_COMMANDS
    assert "gui-web" in GUI_COMMANDS
    assert "voice-parse" in GUI_COMMANDS


def test_shortcut_manifest_targets_native_desktop(tmp_path: Path):
    payload = shortcut_manifest(tmp_path)
    assert payload["primary_mode"] == "native_desktop"
    assert "python launcher.py native-gui" in payload["manual_start"]
    assert payload["web_hud_secondary"] == ["python launcher.py hud", "python launcher.py gui-web"]


def test_native_view_model_exposes_german_voice_and_runtime_truth(tmp_path: Path):
    (tmp_path / "launcher.py").write_text("", encoding="utf-8")
    payload = build_native_view_model(tmp_path)
    assert payload["schema"] == "secondbrain.native.view_model.v30_26"
    assert payload["mode"] == "native_desktop_primary"
    assert payload["web_hud"] == "secondary_only"
    assert payload["voice"]["language"] == "de-DE"
    assert payload["settings"]["schema"] == "secondbrain.gui.settings.embedding.v1"


def test_german_voice_parser_maps_core_commands():
    parser = GermanVoiceCommandParser()
    assert parser.parse("Jarvis Status").intent == "status"
    assert parser.parse("Öffne Dokumente").target == "documents"
    search = parser.parse("Suche nach Telekom Rechnung")
    assert search.intent == "search"
    assert search.command == "p1-rag-hybrid-search"
    repair = parser.parse("Repariere Index")
    assert repair.requires_confirmation is True
    assert repair.command == "p1-vector-index-repair"
