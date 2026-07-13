from __future__ import annotations

from dataclasses import dataclass

from .commands import CommandPalette
from .navigation import NavigationItem, NavigationModel
from .notifications import NotificationCenter
from .router import DesktopRouter
from .state import DesktopState
from .status_service import StatusService
from .view_registry import ViewRegistry


@dataclass(slots=True)
class DesktopShell:
    state: DesktopState
    router: DesktopRouter
    commands: CommandPalette
    notifications: NotificationCenter
    status: StatusService
    views: ViewRegistry
    navigation: NavigationModel

    def open_view(self, view: str) -> object:
        result = self.router.navigate(view)
        self.state.selected_view = view
        return result

    def render_current(self) -> object:
        return self.open_view(self.state.selected_view)

    def sidebar_items(self) -> list[NavigationItem]:
        return self.navigation.sidebar(self.state.selected_view)

    def menu_model(self) -> dict[str, list[str]]:
        groups: dict[str, list[str]] = {}
        for command in self.commands.all():
            groups.setdefault(command.group, []).append(command.title)
        return {group: sorted(titles) for group, titles in sorted(groups.items())}

    def status_line(self) -> str:
        return f"view={self.state.selected_view}; health={self.status.overall()}"
