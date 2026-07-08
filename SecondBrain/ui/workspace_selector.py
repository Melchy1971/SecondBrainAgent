"""Workspace selector model."""

from __future__ import annotations


class WorkspaceSelectorModel:
    def __init__(self, workspaces: list[str] | None = None, current: str | None = None) -> None:
        self._workspaces = list(dict.fromkeys(workspaces or ["default"]))
        self.current = current if current in self._workspaces else self._workspaces[0]

    def list(self) -> list[str]:
        return list(self._workspaces)

    def add(self, name: str) -> None:
        if name and name not in self._workspaces:
            self._workspaces.append(name)

    def switch(self, name: str) -> str:
        if name not in self._workspaces:
            raise ValueError(f"unknown workspace: {name}")
        self.current = name
        return self.current
