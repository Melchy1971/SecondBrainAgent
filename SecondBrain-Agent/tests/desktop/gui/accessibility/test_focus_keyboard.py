from secondbrain.desktop.gui.accessibility.focus_manager import FocusManager
from secondbrain.desktop.gui.accessibility.keyboard_map import KeyboardMap


def test_focus_manager_cycles_forward_and_backward():
    fm = FocusManager()
    fm.register("nav")
    fm.register("content")
    fm.register("status")
    assert fm.active == "nav"
    assert fm.next() == "content"
    assert fm.previous() == "nav"


def test_keyboard_map_resolves_case_insensitive_shortcuts():
    km = KeyboardMap()
    km.defaults()
    action = km.resolve("ctrl+p")
    assert action.command == "open_command_palette"
