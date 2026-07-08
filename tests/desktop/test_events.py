from secondbrain.desktop.events import DesktopEvent, EventBus, EventType


def test_event_bus_publishes_to_subscribers():
    bus = EventBus()
    seen = []
    bus.subscribe(EventType.DOCUMENT_IMPORTED, seen.append)

    event = DesktopEvent(EventType.DOCUMENT_IMPORTED, {"document_id": "d1"})
    bus.publish(event)

    assert seen == [event]
    assert bus.history() == [event]
