from secondbrain.desktop import DesktopApp


def test_app_start_returns_shell_and_pushes_notification(tmp_path):
    app = DesktopApp(tmp_path / "state.json")

    shell = app.start()

    assert app.is_started is True
    assert shell.render_current() == {"view": "dashboard"}
    assert app.notifications.list()[0].title == "Desktop started"


def test_shell_exposes_sidebar_and_menu_model(tmp_path):
    app = DesktopApp(tmp_path / "state.json")
    shell = app.start()

    sidebar_ids = [item.id for item in shell.sidebar_items()]

    assert sidebar_ids[:3] == ["dashboard", "documents", "search"]
    assert "navigation" in shell.menu_model()
    assert "Open Settings" in shell.menu_model()["navigation"]
