from secondbrain.desktop.state import DesktopState, DesktopStateStore


def test_state_roundtrip(tmp_path):
    path = tmp_path / "desktop_state.json"
    store = DesktopStateStore(path)
    state = DesktopState(selected_workspace="w1", selected_view="search", open_tabs=["a"])
    store.save(state)

    loaded = store.load()

    assert loaded.selected_workspace == "w1"
    assert loaded.selected_view == "search"
    assert loaded.open_tabs == ["a"]


def test_state_ignores_invalid_json(tmp_path):
    path = tmp_path / "desktop_state.json"
    path.write_text("{broken", encoding="utf-8")

    assert DesktopStateStore(path).load().selected_view == "dashboard"
