from secondbrain.connectors.incremental_sync import IncrementalSyncEngine
from secondbrain.connectors.event_bus import ConnectorEventBus
from secondbrain.gates.p4_completion_report import build_p4_completion_report


def test_incremental_sync():
    result = IncrementalSyncEngine().compute_changes(["a"], ["a", "b"])
    assert result["added"] == ["b"]


def test_event_bus():
    bus = ConnectorEventBus()
    bus.publish("sync", {"connector": "gmail"})
    assert len(bus.list()) == 1


def test_completion_report():
    report = build_p4_completion_report()
    assert report["status"] == "PASS"
    assert report["next_phase"] == "P5_DESKTOP_GUI"
