from secondbrain.desktop.app import DesktopApp
from secondbrain.desktop.status_service import StatusColor


def test_desktop_app_bootstraps_defaults(tmp_path):
    app = DesktopApp(tmp_path / "state.json")

    assert app.shell.open_view("dashboard") == {"view": "dashboard"}
    assert app.status.overall() == StatusColor.YELLOW
    assert app.commands.execute("open.settings") == {"view": "settings"}
    assert app.state.selected_view == "settings"
