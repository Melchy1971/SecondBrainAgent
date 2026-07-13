from pathlib import Path

from secondbrain.gui.launch import GUI_COMMANDS, gui_doctor, gui_status, shortcut_manifest


def test_gui_commands_include_legacy_and_current_aliases():
    assert {"gui", "gui-start", "gui-open", "desktop-gui", "desktop16-gui", "native-gui", "native-status", "voice-status", "voice-parse", "gui-web", "hud", "gui-status", "gui-doctor", "gui-shortcuts"}.issubset(GUI_COMMANDS)


def test_gui_status_is_safe_when_stopped(tmp_path):
    payload = gui_status(tmp_path)
    assert payload["status"] in {"stopped", "running", "native_ready", "native_blocked"}
    assert payload["url"] == "http://127.0.0.1:8851"
    assert payload["pid_file"].endswith("jarvis_hud.pid")
    assert payload["mode"] == "native_desktop"


def test_gui_doctor_reports_required_start_files(tmp_path):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "launcher.py").write_text("", encoding="utf-8")
    (tmp_path / "scripts" / "start_hud.py").write_text("", encoding="utf-8")
    (tmp_path / "Jarvis.bat").write_text("", encoding="utf-8")
    (tmp_path / "HUD.bat").write_text("", encoding="utf-8")
    (tmp_path / "Install-Jarvis-Desktop.ps1").write_text("", encoding="utf-8")

    payload = gui_doctor(tmp_path)
    assert payload["ok"] is True
    assert payload["status"] == "pass"


def test_shortcut_manifest_documents_manual_start_paths(tmp_path):
    payload = shortcut_manifest(tmp_path)
    assert payload["schema"] == "secondbrain.gui.shortcuts.v1"
    assert any(item["name"] in {"Jarvis", "Jarvis GUI"} for item in payload["desktop_shortcuts"])
    assert "python launcher.py native-gui" in payload["manual_start"]
