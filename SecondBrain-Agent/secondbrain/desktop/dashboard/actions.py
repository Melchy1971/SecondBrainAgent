from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Iterable, Mapping


class DashboardActionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    NOT_FOUND = "not_found"
    DISABLED = "disabled"


class DashboardActionType(str, Enum):
    REFRESH_WIDGET = "refresh_widget"
    OPEN_VIEW = "open_view"
    RUN_COMMAND = "run_command"
    NAVIGATE = "navigate"
    CUSTOM = "custom"


@dataclass(frozen=True, slots=True)
class DashboardAction:
    action_id: str
    label: str
    action_type: DashboardActionType = DashboardActionType.CUSTOM
    widget_id: str | None = None
    enabled: bool = True
    payload: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.action_id:
            errors.append("action_id_required")
        if not self.label:
            errors.append("label_required")
        if self.action_type == DashboardActionType.REFRESH_WIDGET and not self.widget_id:
            errors.append("widget_id_required_for_refresh")
        return errors


@dataclass(frozen=True, slots=True)
class DashboardActionResult:
    action_id: str
    status: DashboardActionStatus
    message: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status == DashboardActionStatus.SUCCESS


ActionHandler = Callable[[DashboardAction], DashboardActionResult | Mapping[str, Any] | None]


class DashboardActionRegistry:
    def __init__(self) -> None:
        self._actions: dict[str, DashboardAction] = {}
        self._handlers: dict[str, ActionHandler] = {}

    def register(self, action: DashboardAction, handler: ActionHandler | None = None) -> None:
        errors = action.validate()
        if errors:
            raise ValueError(",".join(errors))
        self._actions[action.action_id] = action
        if handler is not None:
            self._handlers[action.action_id] = handler

    def unregister(self, action_id: str) -> bool:
        existed = action_id in self._actions
        self._actions.pop(action_id, None)
        self._handlers.pop(action_id, None)
        return existed

    def get(self, action_id: str) -> DashboardAction | None:
        return self._actions.get(action_id)

    def handler_for(self, action_id: str) -> ActionHandler | None:
        return self._handlers.get(action_id)

    def list_actions(self, widget_id: str | None = None) -> list[DashboardAction]:
        actions = list(self._actions.values())
        if widget_id is not None:
            actions = [action for action in actions if action.widget_id == widget_id]
        return sorted(actions, key=lambda action: (action.widget_id or "", action.label, action.action_id))


class DashboardActionExecutor:
    def __init__(self, registry: DashboardActionRegistry) -> None:
        self.registry = registry

    def execute(self, action_id: str) -> DashboardActionResult:
        action = self.registry.get(action_id)
        if action is None:
            return DashboardActionResult(action_id, DashboardActionStatus.NOT_FOUND, "action_not_found")
        if not action.enabled:
            return DashboardActionResult(action_id, DashboardActionStatus.DISABLED, "action_disabled")
        handler = self.registry.handler_for(action_id)
        if handler is None:
            return DashboardActionResult(action_id, DashboardActionStatus.SUCCESS, "action_acknowledged", dict(action.payload))
        try:
            result = handler(action)
        except Exception as exc:  # pragma: no cover - exact exception type is handler-owned
            return DashboardActionResult(action_id, DashboardActionStatus.FAILED, str(exc))
        if isinstance(result, DashboardActionResult):
            return result
        if isinstance(result, Mapping):
            return DashboardActionResult(action_id, DashboardActionStatus.SUCCESS, "action_completed", dict(result))
        return DashboardActionResult(action_id, DashboardActionStatus.SUCCESS, "action_completed")


class DashboardActionService:
    def __init__(self, registry: DashboardActionRegistry | None = None) -> None:
        self.registry = registry or DashboardActionRegistry()
        self.executor = DashboardActionExecutor(self.registry)

    def register_default_widget_actions(self, widget_ids: Iterable[str]) -> None:
        for widget_id in widget_ids:
            self.registry.register(
                DashboardAction(
                    action_id=f"refresh:{widget_id}",
                    label="Refresh",
                    action_type=DashboardActionType.REFRESH_WIDGET,
                    widget_id=widget_id,
                    payload={"widget_id": widget_id},
                )
            )
            self.registry.register(
                DashboardAction(
                    action_id=f"open:{widget_id}",
                    label="Open details",
                    action_type=DashboardActionType.OPEN_VIEW,
                    widget_id=widget_id,
                    payload={"view": widget_id},
                )
            )

    def execute(self, action_id: str) -> DashboardActionResult:
        return self.executor.execute(action_id)
