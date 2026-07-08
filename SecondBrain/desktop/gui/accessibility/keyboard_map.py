from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class KeyboardAction:
    shortcut: str
    command: str
    description: str

class KeyboardMap:
    def __init__(self) -> None:
        self._actions: dict[str, KeyboardAction] = {}

    def register(self, shortcut: str, command: str, description: str) -> None:
        key = shortcut.strip().lower()
        if not key or not command:
            raise ValueError("shortcut and command are required")
        self._actions[key] = KeyboardAction(shortcut=shortcut, command=command, description=description)

    def resolve(self, shortcut: str) -> KeyboardAction | None:
        return self._actions.get(shortcut.strip().lower())

    def defaults(self) -> None:
        self.register("Ctrl+P", "open_command_palette", "Befehlspalette öffnen")
        self.register("Ctrl+F", "focus_search", "Suche fokussieren")
        self.register("Esc", "close_overlay", "Overlay schließen")
        self.register("F5", "refresh_active_view", "Aktive Ansicht aktualisieren")
