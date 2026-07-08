"""v30.46.3 - Tests fuer die Vier-Zonen-Workspace-Shell.

Panel-Logik wird headless getestet; der Tk-Smoke-Test laeuft nur,
wenn ein Display verfuegbar ist (CI-sicher).
"""
from __future__ import annotations

import tkinter as tk

import pytest

from secondbrain.native.ai_workspace.panels import NAVIGATION_PRIMARY, PromptBar


class _Module:
    def __init__(self, module_id: str, title: str) -> None:
        self.id = module_id
        self.title = title


def test_navigation_primary_covers_briefing_zones() -> None:
    assert NAVIGATION_PRIMARY == ("dashboard", "workspace", "documents", "memory", "agents", "voice")


def test_prompt_bar_normalizes_and_validates() -> None:
    assert PromptBar.normalize_prompt("  Frage  ") == "Frage"
    assert PromptBar.normalize_prompt("   ") == ""
    assert PromptBar.validate_provider("OpenAI") == "openai"
    assert PromptBar.validate_provider("unbekannt") == "ollama"


def test_voice_module_lookup_uses_existing_navigation() -> None:
    modules = [_Module("dashboard", "Dashboard"), _Module("voice", "Voice Control")]
    assert PromptBar.voice_module_id(modules) == "voice"
    assert PromptBar.voice_module_id([_Module("x", "Sprachsteuerung")]) == "x"
    assert PromptBar.voice_module_id([_Module("dashboard", "Dashboard")]) is None


def _display_available() -> bool:
    try:
        root = tk.Tk()
    except tk.TclError:
        return False
    root.destroy()
    return True


@pytest.mark.skipif(not _display_available(), reason="kein Display verfuegbar")
def test_workspace_shell_builds_four_zones(tmp_path) -> None:
    from secondbrain.native.ai_workspace.gui import AIWorkspaceApp

    app = AIWorkspaceApp(tmp_path)
    try:
        # eine Navigation, eine Toolbar, rechtes Panel, Bottom-Bar
        assert app.navigation.winfo_exists()
        assert app.toolbar.winfo_exists()
        assert app.right_panel.winfo_exists()
        assert app.bottom_bar.winfo_exists()
        tabs = [app.right_panel.notebook.tab(tab_id, "text") for tab_id in app.right_panel.notebook.tabs()]
        assert tabs == ["Quellen", "Memory", "Dokumente", "Runtime"]
    finally:
        app.destroy()
