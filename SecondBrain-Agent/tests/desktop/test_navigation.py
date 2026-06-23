from secondbrain.desktop import DesktopView, NavigationModel, ViewRegistry


def test_navigation_model_marks_active_view():
    registry = ViewRegistry()
    registry.register(DesktopView("dashboard", "Dashboard", lambda: None, icon="home", order=1))
    registry.register(DesktopView("hidden", "Hidden", lambda: None, visible=False, order=2))
    navigation = NavigationModel(registry)

    items = navigation.sidebar("dashboard")

    assert [item.id for item in items] == ["dashboard"]
    assert items[0].active is True
    assert items[0].icon == "home"
