from secondbrain.mobile_companion import MobileCompanionRuntime


def test_status(tmp_path):
    rt = MobileCompanionRuntime(tmp_path)
    assert rt.status()["version"] == "16.9"


def test_pairing(tmp_path):
    rt = MobileCompanionRuntime(tmp_path)
    req = rt.pair_request("iPhone", "ios")
    approved = rt.approve_pairing(req["id"])
    assert approved["ok"] is True
    assert rt.devices()


def test_capture_replay(tmp_path):
    rt = MobileCompanionRuntime(tmp_path)
    rt.voice_note("Jarvis Notiz")
    rt.camera_ocr("image://demo")
    assert len(rt.offline_queue()) == 2
    assert rt.replay_offline()["replayed"] == 2


def test_push_widgets_sync(tmp_path):
    rt = MobileCompanionRuntime(tmp_path)
    rt.push("A", "B")
    assert rt.deliver_push()["delivered"] == 1
    assert rt.widget_enable("today", False)["enabled"] == 0
    assert rt.sync()["status"] == "success"


def test_session_manifest(tmp_path):
    rt = MobileCompanionRuntime(tmp_path)
    rt.session_create("Continue Chat")
    assert rt.sessions()
    assert "iOS" in rt.app_manifest()["targets"]
