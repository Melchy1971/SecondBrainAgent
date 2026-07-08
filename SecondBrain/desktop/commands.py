from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True, slots=True)
class Command:
    id: str
    title: str
    action: Callable[[], object]
    shortcut: str | None = None
    group: str = "general"


class CommandPalette:
    def __init__(self) -> None:
        self._commands: dict[str, Command] = {}

    def register(self, command: Command) -> None:
        if not command.id:
            raise ValueError("command id must not be empty")
        self._commands[command.id] = command

    def execute(self, command_id: str) -> object:
        if command_id not in self._commands:
            raise KeyError(f"unknown command: {command_id}")
        return self._commands[command_id].action()

    def search(self, query: str) -> list[Command]:
        needle = query.strip().lower()
        commands = list(self._commands.values())
        if not needle:
            return commands
        return [command for command in commands if needle in command.title.lower() or needle in command.id.lower()]

    def all(self) -> list[Command]:
        return list(self._commands.values())
