from secondbrain.agent.planning.planning_events import PlanningEventBus


def test_event_bus_records_and_notifies():
    bus = PlanningEventBus()
    seen = []
    bus.subscribe(seen.append)

    event = bus.publish("TASK_STARTED", {"task_id": "t1"})

    assert bus.events == [event]
    assert seen == [event]
