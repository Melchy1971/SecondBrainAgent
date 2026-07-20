import sys
import types

from secondbrain.desktop_native.tray import SystemTrayController, tray_status_text


def controller(calls):
    return SystemTrayController(
        on_open=lambda: calls.append("open"),
        on_toggle_listening=lambda: calls.append("listen"),
        on_toggle_mute=lambda: calls.append("mute"),
        on_push_to_talk=lambda: calls.append("ptt"),
        on_exit=lambda: calls.append("exit"),
        status_text=lambda: "Status: READY",
    )


def test_missing_optional_dependencies_is_degraded(monkeypatch):
    monkeypatch.setattr("secondbrain.desktop_native.tray.find_spec", lambda _name: None)
    result = controller([]).start()
    assert result.available is False
    assert result.running is False


def test_tray_status_text_includes_cached_approval_activity():
    assert tray_status_text(status="READY", voice="IDLE", approvals="2 Pending / 1 Overdue") == (
        "Status: READY · Voice: IDLE · Approvals: 2 Pending / 1 Overdue"
    )


def test_tray_menu_callbacks_and_shutdown(monkeypatch):
    calls = []
    made = {}

    class Item:
        def __init__(self, text, action, **kwargs):
            self.text, self.action = text, action

    class Icon:
        def __init__(self, name, image, title, menu):
            made["icon"], self.menu, self.stopped = self, menu, False
        def run_detached(self):
            made["detached"] = True
        def stop(self):
            self.stopped = True

    fake_pystray = types.SimpleNamespace(Menu=lambda *items: items, MenuItem=Item, Icon=Icon)
    fake_image = types.SimpleNamespace(new=lambda *args: object())
    fake_draw = types.SimpleNamespace(Draw=lambda image: types.SimpleNamespace(ellipse=lambda *args, **kwargs: None))
    monkeypatch.setitem(sys.modules, "pystray", fake_pystray)
    monkeypatch.setitem(sys.modules, "PIL", types.SimpleNamespace(Image=fake_image, ImageDraw=fake_draw))
    monkeypatch.setattr("secondbrain.desktop_native.tray.find_spec", lambda _name: object())
    tray = controller(calls)
    assert tray.start().running is True
    icon = made["icon"]
    icon.menu[0].action(None, None)
    icon.menu[3].action(None, None)
    icon.menu[4].action(None, None)
    icon.menu[2].action(None, None)
    icon.menu[5].action(None, None)
    assert calls == ["open", "mute", "ptt", "listen", "exit"]
    tray.stop()
    assert icon.stopped is True
