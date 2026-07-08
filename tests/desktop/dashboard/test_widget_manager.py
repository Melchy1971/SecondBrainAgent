from secondbrain.desktop.dashboard import DashboardWidget, WidgetManager, WidgetRegistry, WidgetStatus


def test_refresh_uses_provider_data():
    registry = WidgetRegistry()
    registry.register(DashboardWidget(widget_id="rag", title="RAG"), lambda workspace: {"workspace": workspace, "ok": True})
    manager = WidgetManager(registry)

    widget = manager.refresh("rag", "w1")

    assert widget.status == WidgetStatus.READY
    assert widget.data == {"workspace": "w1", "ok": True}


def test_refresh_isolates_provider_failure():
    def failing(_workspace):
        raise RuntimeError("boom")

    registry = WidgetRegistry()
    registry.register(DashboardWidget(widget_id="bad", title="Bad"), failing)
    manager = WidgetManager(registry)

    widget = manager.refresh("bad")

    assert widget.status == WidgetStatus.FAILED
    assert widget.error == "boom"
