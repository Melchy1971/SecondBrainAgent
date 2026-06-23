import pytest

from secondbrain.desktop import DesktopView, ViewRegistry


def test_view_registry_orders_visible_views():
    registry = ViewRegistry()
    registry.register(DesktopView("settings", "Settings", lambda: "settings", order=90))
    registry.register(DesktopView("dashboard", "Dashboard", lambda: "dashboard", order=10))

    assert [view.id for view in registry.all(visible_only=True)] == ["dashboard", "settings"]
    assert registry.render("dashboard") == "dashboard"


def test_view_registry_rejects_duplicate_view():
    registry = ViewRegistry()
    registry.register(DesktopView("dashboard", "Dashboard", lambda: None))

    with pytest.raises(ValueError):
        registry.register(DesktopView("dashboard", "Dashboard 2", lambda: None))
