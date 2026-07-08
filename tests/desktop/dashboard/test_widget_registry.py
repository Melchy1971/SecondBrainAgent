import pytest

from secondbrain.desktop.dashboard import DashboardWidget, WidgetRegistry
from secondbrain.desktop.dashboard.widget_registry import WidgetRegistryError


def test_registers_widget_and_rejects_duplicate():
    registry = WidgetRegistry()
    registry.register(DashboardWidget(widget_id="jobs", title="Jobs"))

    assert registry.ids() == ["jobs"]

    with pytest.raises(WidgetRegistryError):
        registry.register(DashboardWidget(widget_id="jobs", title="Jobs Duplicate"))


def test_enabled_filters_disabled_widgets():
    registry = WidgetRegistry()
    registry.register(DashboardWidget(widget_id="a", title="A"))
    registry.register(DashboardWidget(widget_id="b", title="B", enabled=False))

    assert [widget.widget_id for widget in registry.enabled()] == ["a"]
