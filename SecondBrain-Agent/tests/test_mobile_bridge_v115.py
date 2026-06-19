
from pathlib import Path
import pytest

from secondbrain.mobile_bridge_v115 import MobileBridge
from secondbrain.launcher_runtime_v115 import SecondBrainLauncherV115


def test_register_and_status(tmp_path: Path):
    bridge = MobileBridge(tmp_path)
    device = bridge.register_device("iPhone", "ios", trusted=True)
    status = bridge.status()
    assert device["platform"] == "ios"
    assert status["devices"] == 1
    assert status["trusted_devices"] == 1


def test_push_capture_and_delivery(tmp_path: Path):
    bridge = MobileBridge(tmp_path)
    device = bridge.register_device("Pixel", "android")
    msg = bridge.enqueue_push(device["device_id"], "Hallo", "Test")
    capture = bridge.submit_capture(device["device_id"], "note", "Idee", "Inhalt")
    delivered = bridge.mark_push_delivered(msg["message_id"])
    assert delivered["status"] == "delivered"
    assert capture["processed"] is False
    assert len(bridge.list_captures(unprocessed_only=True)) == 1


def test_approval_requires_trusted_device(tmp_path: Path):
    bridge = MobileBridge(tmp_path)
    device = bridge.register_device("Web", "web", trusted=False)
    with pytest.raises(PermissionError):
        bridge.request_approval(device["device_id"], "system.restart", {}, "Restart?", 4)
    bridge.trust_device(device["device_id"], True)
    approval = bridge.request_approval(device["device_id"], "system.restart", {}, "Restart?", 4)
    decided = bridge.decide_approval(approval["approval_id"], "approved")
    assert decided["status"] == "approved"


def test_launcher_mobile_commands(tmp_path: Path):
    launcher = SecondBrainLauncherV115(tmp_path)
    device = launcher.mobile_register("iPhone", "ios", trusted=True)
    push = launcher.mobile_push(device["device_id"], "Jarvis", "Bereit")
    capture = launcher.mobile_capture(device["device_id"], "task", "Aufgabe", "RAG prüfen")
    approval = launcher.mobile_approval_request(device["device_id"], "agent.execute", "Agent ausführen", risk=3)
    assert launcher.mobile_status()["devices"] == 1
    assert push["status"] == "queued"
    assert capture["capture_type"] == "task"
    assert approval["status"] == "pending"
