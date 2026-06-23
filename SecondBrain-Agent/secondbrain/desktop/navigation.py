from __future__ import annotations

from dataclasses import dataclass

from .view_registry import DesktopView, ViewRegistry


@dataclass(frozen=True, slots=True)
class NavigationItem:
    id: str
    title: str
    icon: str = ""
    active: bool = False


class NavigationModel:
    def __init__(self, registry: ViewRegistry) -> None:
        self.registry = registry

    def sidebar(self, active_view: str | None = None) -> list[NavigationItem]:
        return [self._to_item(view, active_view) for view in self.registry.all(visible_only=True)]

    @staticmethod
    def _to_item(view: DesktopView, active_view: str | None) -> NavigationItem:
        return NavigationItem(
            id=view.id,
            title=view.title,
            icon=view.icon,
            active=view.id == active_view,
        )
