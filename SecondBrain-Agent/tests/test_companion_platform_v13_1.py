from secondbrain.companion_platform import CompanionPlatform


def test_status_empty(tmp_path):
    cp = CompanionPlatform(tmp_path)
    status = cp.status()
    assert status["devices"] == 0
    assert status["sync"]["protocol"] == "local-sync-v2"


def test_pairing_flow(tmp_path):
    cp = CompanionPlatform(tmp_path)
    req = cp.devices.pair_request("iPhone", "ios")
    approved = cp.devices.approve_pairing(req["id"])
    assert approved["ok"] is True
    assert len(cp.devices.devices()) == 1
    assert cp.devices.devices()[0]["trust_level"] == "trusted"


def test_sync_and_offline(tmp_path):
    cp = CompanionPlatform(tmp_path)
    cp.offline.capture("phone", "note", {"text": "hello"})
    assert len(cp.offline.queue()) == 1
    replayed = cp.offline.replay()
    assert replayed[0]["status"] == "replayed"
    sync = cp.sync.sync_now("phone")
    assert sync["status"] == "success"


def test_push_delivery(tmp_path):
    cp = CompanionPlatform(tmp_path)
    cp.push.send("A", "B")
    assert len(cp.push.outbox()) == 1
    delivered = cp.push.deliver()
    assert delivered[0]["status"] == "delivered"
    assert len(cp.push.outbox()) == 0


def test_sessions_widgets_web(tmp_path):
    cp = CompanionPlatform(tmp_path)
    session = cp.sessions.create("Chat", "desktop")
    resumed = cp.sessions.resume(session["id"], "phone")
    assert resumed["resumed_on"] == "phone"
    widget = cp.widgets.set_enabled("today", False)
    assert widget["enabled"] is False
    assert cp.web.start()["status"] == "running"
