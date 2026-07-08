from secondbrain.desktop.events import EventBus, EventType
from secondbrain.desktop.job_feedback import JobFeedbackCenter, JobState
from secondbrain.desktop.notifications import NotificationCenter, NotificationLevel
from secondbrain.desktop.status_service import StatusColor, StatusService


def make_center():
    events = EventBus()
    notifications = NotificationCenter()
    status = StatusService()
    center = JobFeedbackCenter(events, notifications, status)
    return center, events, notifications, status


def test_start_creates_running_job_and_side_effects():
    center, events, notifications, status = make_center()

    job = center.start("Import File", metadata={"path": "a.md"})

    assert job.state == JobState.RUNNING
    assert job.progress == 0.0
    assert center.get(job.id) == job
    assert status.get_status("Jobs").color == StatusColor.YELLOW
    assert events.history()[-1].type == EventType.JOB_STARTED
    assert notifications.list()[-1].level == NotificationLevel.INFO


def test_progress_is_bounded_and_keeps_job_running():
    center, _, _, status = make_center()
    job = center.start("Index")

    updated = center.progress(job.id, 1.7, "almost")

    assert updated.progress == 1.0
    assert updated.state == JobState.RUNNING
    assert status.get_status("Jobs").message == "Index 100%"


def test_succeed_marks_terminal_and_restores_idle_status():
    center, events, notifications, status = make_center()
    job = center.start("Sync")

    updated = center.succeed(job.id)

    assert updated.state == JobState.SUCCEEDED
    assert updated.terminal is True
    assert status.get_status("Jobs").color == StatusColor.GREEN
    assert events.history()[-1].payload["ok"] is True
    assert notifications.list()[-1].level == NotificationLevel.SUCCESS


def test_fail_emits_error_event_and_red_status():
    center, events, notifications, status = make_center()
    job = center.start("Connector")

    updated = center.fail(job.id, "timeout")

    assert updated.state == JobState.FAILED
    assert status.get_status("Jobs").color == StatusColor.RED
    assert [event.type for event in events.history()][-2:] == [EventType.ERROR_OCCURRED, EventType.JOB_FINISHED]
    assert notifications.list()[-1].level == NotificationLevel.ERROR


def test_cancel_marks_terminal_without_red_status():
    center, events, notifications, status = make_center()
    job = center.start("Long Task")

    updated = center.cancel(job.id)

    assert updated.state == JobState.CANCELLED
    assert updated.terminal is True
    assert status.get_status("Jobs").color == StatusColor.GREEN
    assert events.history()[-1].payload["cancelled"] is True
    assert notifications.list()[-1].level == NotificationLevel.WARNING


def test_active_only_filters_terminal_jobs():
    center, _, _, _ = make_center()
    done = center.start("Done")
    active = center.start("Active")
    center.succeed(done.id)

    assert center.list(active_only=True) == [center.get(active.id)]


def test_unknown_job_raises_key_error():
    center, _, _, _ = make_center()

    try:
        center.succeed("missing")
    except KeyError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("expected KeyError")
