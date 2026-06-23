from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .commands import CommandPalette
from .events import DesktopEvent, EventBus, EventType
from .notifications import NotificationCenter, NotificationLevel
from .status_service import StatusColor, StatusService


@dataclass(frozen=True, slots=True)
class CommandExecutionResult:
    command_id: str
    ok: bool
    value: Any = None
    error: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def failed(self) -> bool:
        return not self.ok


class DesktopCommandExecutor:
    """Executes command palette entries with uniform events, notifications and status updates.

    The executor is intentionally UI-toolkit agnostic. GUI layers can bind buttons,
    shortcuts or command-palette selections to this service without duplicating error
    handling and telemetry semantics.
    """

    def __init__(
        self,
        palette: CommandPalette,
        events: EventBus,
        notifications: NotificationCenter,
        status: StatusService,
        status_name: str = "Commands",
    ) -> None:
        self.palette = palette
        self.events = events
        self.notifications = notifications
        self.status = status
        self.status_name = status_name
        self._history: list[CommandExecutionResult] = []
        self.status.set_status(status_name, StatusColor.GREEN, "ready")

    def execute(self, command_id: str) -> CommandExecutionResult:
        started_at = datetime.now(timezone.utc)
        self.events.publish(DesktopEvent(EventType.JOB_STARTED, {"command_id": command_id}))
        self.status.set_status(self.status_name, StatusColor.YELLOW, f"running {command_id}")
        try:
            value = self.palette.execute(command_id)
        except Exception as exc:  # noqa: BLE001 - desktop command boundary must isolate failures
            result = CommandExecutionResult(
                command_id=command_id,
                ok=False,
                error=f"{type(exc).__name__}: {exc}",
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
            )
            self._history.append(result)
            self.status.set_status(self.status_name, StatusColor.RED, result.error or "command failed")
            self.notifications.push("Command failed", result.error or command_id, NotificationLevel.ERROR)
            self.events.publish(
                DesktopEvent(
                    EventType.ERROR_OCCURRED,
                    {"command_id": command_id, "error": result.error},
                )
            )
            self.events.publish(DesktopEvent(EventType.JOB_FINISHED, {"command_id": command_id, "ok": False}))
            return result

        result = CommandExecutionResult(
            command_id=command_id,
            ok=True,
            value=value,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
        )
        self._history.append(result)
        self.status.set_status(self.status_name, StatusColor.GREEN, f"finished {command_id}")
        self.notifications.push("Command completed", command_id, NotificationLevel.SUCCESS)
        self.events.publish(DesktopEvent(EventType.JOB_FINISHED, {"command_id": command_id, "ok": True}))
        return result

    def history(self, limit: int | None = None) -> list[CommandExecutionResult]:
        if limit is None:
            return list(self._history)
        return list(self._history[-limit:])
