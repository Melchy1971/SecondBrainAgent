from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True, slots=True)
class Route:
    name: str
    title: str
    handler: Callable[[], object]


class DesktopRouter:
    def __init__(self, default_route: str = "dashboard") -> None:
        self.default_route = default_route
        self._routes: dict[str, Route] = {}
        self._current = default_route

    @property
    def current(self) -> str:
        return self._current

    def register(self, name: str, title: str, handler: Callable[[], object]) -> None:
        if not name:
            raise ValueError("route name must not be empty")
        self._routes[name] = Route(name=name, title=title, handler=handler)

    def navigate(self, name: str) -> object:
        if name not in self._routes:
            raise KeyError(f"unknown route: {name}")
        self._current = name
        return self._routes[name].handler()

    def routes(self) -> list[Route]:
        return list(self._routes.values())
