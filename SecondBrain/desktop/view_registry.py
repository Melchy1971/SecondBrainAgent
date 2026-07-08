from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable


ViewFactory = Callable[[], object]


@dataclass(frozen=True, slots=True)
class DesktopView:
    id: str
    title: str
    factory: ViewFactory
    icon: str = ""
    order: int = 100
    visible: bool = True


class ViewRegistry:
    def __init__(self) -> None:
        self._views: dict[str, DesktopView] = {}

    def register(self, view: DesktopView) -> None:
        view_id = view.id.strip()
        if not view_id:
            raise ValueError("view id must not be empty")
        if view_id in self._views:
            raise ValueError(f"duplicate view: {view_id}")
        self._views[view_id] = DesktopView(
            id=view_id,
            title=view.title.strip() or view_id.title(),
            factory=view.factory,
            icon=view.icon,
            order=view.order,
            visible=view.visible,
        )

    def get(self, view_id: str) -> DesktopView:
        try:
            return self._views[view_id]
        except KeyError as exc:
            raise KeyError(f"unknown view: {view_id}") from exc

    def render(self, view_id: str) -> object:
        return self.get(view_id).factory()

    def all(self, visible_only: bool = False) -> list[DesktopView]:
        views: Iterable[DesktopView] = self._views.values()
        if visible_only:
            views = [view for view in views if view.visible]
        return sorted(views, key=lambda view: (view.order, view.title.lower(), view.id))
