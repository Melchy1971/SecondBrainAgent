from datetime import datetime, timedelta, timezone

from secondbrain.desktop.dashboard import DashboardWidget, RefreshScheduler, WidgetManager, WidgetRegistry


def test_due_widgets_include_never_refreshed_and_elapsed_interval():
    registry = WidgetRegistry()
    manager = WidgetManager(registry)
    scheduler = RefreshScheduler(manager)
    now = datetime.now(timezone.utc)
    fresh = DashboardWidget(widget_id="fresh", title="Fresh", refresh_interval=60, last_refresh=now)
    old = DashboardWidget(widget_id="old", title="Old", refresh_interval=60, last_refresh=now - timedelta(seconds=61))
    new = DashboardWidget(widget_id="new", title="New")

    assert [w.widget_id for w in scheduler.due_widgets([fresh, old, new], now=now)] == ["old", "new"]
