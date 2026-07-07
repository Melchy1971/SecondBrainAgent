from __future__ import annotations

from secondbrain.agent.coordination import CommunicationBus


def test_publish_and_log():
    bus = CommunicationBus()
    bus.publish("topic.a", "sender1", {"x": 1})
    bus.publish("topic.b", "sender2", {"y": 2})
    assert len(bus.log) == 2
    assert bus.messages("topic.a")[0].payload == {"x": 1}


def test_subscribers_receive_messages():
    bus = CommunicationBus()
    received = []
    bus.subscribe("work", lambda m: received.append(m.payload))
    bus.subscribe("work", lambda m: received.append({"seen": True}))
    results = bus.publish("work", "coordinator", {"task": "do"})
    assert len(results) == 2
    assert {"task": "do"} in received
    assert {"seen": True} in received


def test_messages_filtered_by_topic():
    bus = CommunicationBus()
    bus.publish("a", "s", {})
    bus.publish("b", "s", {})
    bus.publish("a", "s", {})
    assert len(bus.messages("a")) == 2
    assert len(bus.messages()) == 3


def test_bus_persists_when_project_root_given(tmp_path):
    bus = CommunicationBus(tmp_path)
    bus.publish("t", "s", {"k": "v"})
    path = tmp_path / "runtime" / "agent" / "coordination" / "bus.jsonl"
    assert path.exists()
    assert "\"k\": \"v\"" in path.read_text(encoding="utf-8")
