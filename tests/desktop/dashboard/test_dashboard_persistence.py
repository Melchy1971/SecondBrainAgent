from secondbrain.desktop.dashboard import DashboardPersistence, DashboardState, DashboardWidget, WidgetStatus


def test_state_roundtrip(tmp_path):
    persistence = DashboardPersistence(tmp_path)
    state = DashboardState(active_layout="ops", enabled_widgets=["a"], selected_workspace="w2")
    state.touch()

    persistence.save_state(state)
    loaded = persistence.load_state()

    assert loaded.active_layout == "ops"
    assert loaded.enabled_widgets == ["a"]
    assert loaded.selected_workspace == "w2"
    assert loaded.last_update is not None


def test_widget_roundtrip(tmp_path):
    persistence = DashboardPersistence(tmp_path)
    widget = DashboardWidget(widget_id="health", title="Health", status=WidgetStatus.READY, data={"green": 3})
    widget.mark_ready({"green": 3})

    persistence.save_widgets([widget])
    loaded = persistence.load_widgets()

    assert loaded[0].widget_id == "health"
    assert loaded[0].status == WidgetStatus.READY
    assert loaded[0].data == {"green": 3}
