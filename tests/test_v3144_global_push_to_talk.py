import pytest

from secondbrain.desktop_native.hotkey import GlobalPushToTalkHotkey


class FakeListener:
    def __init__(self, bindings):
        self.bindings = bindings
        self.started = False
        self.stopped = False

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True


def test_disabled_hotkey_does_not_start_or_record_keys():
    hotkey = GlobalPushToTalkHotkey(lambda: None, listener_factory=FakeListener)
    assert hotkey.start() is False
    assert hotkey.status()["raw_keys_recorded"] is False


def test_listener_failure_keeps_desktop_in_degraded_mode():
    class FailingListener(FakeListener):
        def start(self):
            raise RuntimeError("hotkey already registered")

    hotkey = GlobalPushToTalkHotkey(lambda: None, enabled=True, listener_factory=FailingListener)
    assert hotkey.start() is False
    assert hotkey.running is False
    assert hotkey.status()["last_error"] == "hotkey already registered"


def test_configured_chord_invokes_only_push_to_talk_callback():
    calls = []
    hotkey = GlobalPushToTalkHotkey(lambda: calls.append("ptt"), enabled=True, listener_factory=FakeListener)
    assert hotkey.start() is True
    listener = hotkey._listener
    listener.bindings["<ctrl>+<alt>+j"]()
    assert calls == ["ptt"]
    assert hotkey.activations == 1
    hotkey.stop()
    assert listener.stopped is True


@pytest.mark.parametrize("value", ["j", "ctrl+j", "<ctrl>+<unknown>+j", "<ctrl>+<alt>+delete", ""])
def test_invalid_or_overbroad_hotkeys_are_rejected(value):
    with pytest.raises(ValueError, match="Ungültiger"):
        GlobalPushToTalkHotkey(lambda: None, hotkey=value)
