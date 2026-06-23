from __future__ import annotations

from secondbrain.desktop.command_executor import DesktopCommandExecutor
from secondbrain.desktop.commands import Command, CommandPalette
from secondbrain.desktop.events import EventBus, EventType
from secondbrain.desktop.notifications import NotificationCenter, NotificationLevel
from secondbrain.desktop.status_service import StatusColor, StatusService


def build_executor() -> tuple[CommandPalette, EventBus, NotificationCenter, StatusService, DesktopCommandExecutor]:
    palette = CommandPalette()
    events = EventBus()
    notifications = NotificationCenter()
    status = StatusService()
    executor = DesktopCommandExecutor(palette, events, notifications, status)
    return palette, events, notifications, status, executor


def test_execute_success_publishes_lifecycle_and_success_notification() -> None:
    palette, events, notifications, status, executor = build_executor()
    palette.register(Command("demo.ok", "Demo OK", lambda: {"ok": True}))

    result = executor.execute("demo.ok")

    assert result.ok is True
    assert result.value == {"ok": True}
    assert status.get_status("Commands").color == StatusColor.GREEN  # type: ignore[union-attr]
    assert notifications.list()[-1].level == NotificationLevel.SUCCESS
    assert [event.type for event in events.history()] == [EventType.JOB_STARTED, EventType.JOB_FINISHED]


def test_execute_unknown_command_isolated_as_error_result() -> None:
    _, events, notifications, status, executor = build_executor()

    result = executor.execute("missing.command")

    assert result.failed is True
    assert "KeyError" in (result.error or "")
    assert status.get_status("Commands").color == StatusColor.RED  # type: ignore[union-attr]
    assert notifications.list()[-1].level == NotificationLevel.ERROR
    assert [event.type for event in events.history()] == [
        EventType.JOB_STARTED,
        EventType.ERROR_OCCURRED,
        EventType.JOB_FINISHED,
    ]


def test_execute_handler_exception_does_not_break_executor() -> None:
    palette, _, _, status, executor = build_executor()

    def broken() -> object:
        raise RuntimeError("boom")

    palette.register(Command("demo.fail", "Demo Fail", broken))
    palette.register(Command("demo.after", "Demo After", lambda: "after"))

    failed = executor.execute("demo.fail")
    recovered = executor.execute("demo.after")

    assert failed.failed is True
    assert recovered.ok is True
    assert recovered.value == "after"
    assert status.get_status("Commands").color == StatusColor.GREEN  # type: ignore[union-attr]


def test_history_limit_returns_latest_results() -> None:
    palette, _, _, _, executor = build_executor()
    palette.register(Command("a", "A", lambda: "a"))
    palette.register(Command("b", "B", lambda: "b"))
    palette.register(Command("c", "C", lambda: "c"))

    executor.execute("a")
    executor.execute("b")
    executor.execute("c")

    assert [item.command_id for item in executor.history(limit=2)] == ["b", "c"]
