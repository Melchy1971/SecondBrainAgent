import pytest
from secondbrain.ui.states import ViewState, AsyncState
from secondbrain.ui.keymap import Keymap, KeymapError
from secondbrain.ui.responsive import layout_for


def test_view_state_transitions():
    v = ViewState()
    assert v.state is AsyncState.IDLE
    v.start("loading"); assert v.is_loading and v.progress == 0.0
    v.set_progress(2.0); assert v.progress == 1.0
    v.succeed({"x": 1}); assert v.state is AsyncState.SUCCESS and v.to_dict()["has_data"]
    v.fail("boom"); assert v.is_error and v.error == "boom"


def test_keymap_defaults_no_conflicts_and_normalize():
    km = Keymap()
    assert km.conflicts() == []
    assert km.key_for("command_palette") == "Ctrl+K"
    assert km.action_for("Shift+Ctrl+L") == "toggle_theme"    # normalized order


def test_keymap_conflict_raises():
    km = Keymap({"a": "Ctrl+K"})
    with pytest.raises(KeymapError):
        km.bind("b", "Ctrl+K")


@pytest.mark.parametrize("width,mode,sidebar,cols", [
    (600, "compact", "collapsed", 1),
    (1000, "regular", "expanded", 2),
    (1600, "wide", "expanded", 3),
])
def test_responsive_breakpoints(width, mode, sidebar, cols):
    layout = layout_for(width)
    assert (layout.mode, layout.sidebar, layout.columns) == (mode, sidebar, cols)
