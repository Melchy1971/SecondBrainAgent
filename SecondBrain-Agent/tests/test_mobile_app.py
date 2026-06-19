from secondbrain.mobile_app import MobileAppRuntime


def test_register_and_status(tmp_path):
    app = MobileAppRuntime(tmp_path)
    app.devices.register("iphone", "iPhone Markus", "ios", True, True)
    status = app.status()
    assert status["devices"] == 1
    assert status["trusted_devices"] == 1


def test_untrusted_command_blocked(tmp_path):
    app = MobileAppRuntime(tmp_path)
    app.devices.register("x", "Unknown", "android", False, False)
    result = app.secure_command("x", "capture", {"text": "test"})
    assert result["ok"] is False


def test_trusted_command_queued(tmp_path):
    app = MobileAppRuntime(tmp_path)
    app.devices.register("iphone", "iPhone", "ios", True, True)
    result = app.secure_command("iphone", "capture", {"text": "test"})
    assert result["ok"] is True
    assert len(app.queue.items()) == 1


def test_push_and_widgets(tmp_path):
    app = MobileAppRuntime(tmp_path)
    app.push.send("A", "B")
    assert len(app.push.list()) == 1
    assert len(app.widgets.widgets()) >= 3
