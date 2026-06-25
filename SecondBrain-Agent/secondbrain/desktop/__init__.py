"""Public desktop foundation API."""

from .app import DesktopApp
from .command_executor import CommandExecutionResult, DesktopCommandExecutor
from .commands import Command, CommandPalette
from .events import DesktopEvent, EventBus, EventType
from .job_feedback import JobFeedback, JobFeedbackCenter, JobState
from .navigation import NavigationItem, NavigationModel
from .notifications import Notification, NotificationCenter, NotificationLevel
from .router import DesktopRouter, Route
from .shell import DesktopShell
from .state import DesktopState, DesktopStateStore
from .status_service import ServiceStatus, StatusColor, StatusService
from .view_registry import DesktopView, ViewRegistry
from .workspace_manager import WorkspaceManager

__all__ = [
    "Command",
    "CommandExecutionResult",
    "CommandPalette",
    "DesktopApp",
    "DesktopCommandExecutor",
    "DesktopEvent",
    "DesktopRouter",
    "DesktopShell",
    "DesktopState",
    "DesktopStateStore",
    "DesktopView",
    "EventBus",
    "EventType",
    "JobFeedback",
    "JobFeedbackCenter",
    "JobState",
    "NavigationItem",
    "NavigationModel",
    "Notification",
    "NotificationCenter",
    "NotificationLevel",
    "Route",
    "ServiceStatus",
    "StatusColor",
    "StatusService",
    "ViewRegistry",
    "WorkspaceManager",
]
