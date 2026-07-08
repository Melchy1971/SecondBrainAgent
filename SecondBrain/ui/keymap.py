"""Keyboard navigation registry with conflict detection."""

from __future__ import annotations


DEFAULT_BINDINGS = {
    "command_palette": "Ctrl+K",
    "global_search": "Ctrl+F",
    "toggle_theme": "Ctrl+Shift+L",
    "toggle_sidebar": "Ctrl+B",
    "next_panel": "Ctrl+Tab",
    "prev_panel": "Ctrl+Shift+Tab",
    "close_window": "Ctrl+W",
    "focus_workspace_selector": "Ctrl+P",
}


class KeymapError(ValueError):
    pass


class Keymap:
    def __init__(self, bindings: dict[str, str] | None = None) -> None:
        self._bindings: dict[str, str] = {}
        for action, key in (bindings or DEFAULT_BINDINGS).items():
            self.bind(action, key)

    @staticmethod
    def _normalize(key: str) -> str:
        parts = [p.strip().capitalize() for p in key.replace(" ", "").split("+") if p.strip()]
        order = {"Ctrl": 0, "Alt": 1, "Shift": 2}
        mods = sorted([p for p in parts if p in order], key=lambda m: order[m])
        keys = [p for p in parts if p not in order]
        return "+".join(mods + keys)

    def bind(self, action: str, key: str) -> None:
        norm = self._normalize(key)
        for existing_action, existing_key in self._bindings.items():
            if existing_key == norm and existing_action != action:
                raise KeymapError(f"key {norm!r} already bound to {existing_action!r}")
        self._bindings[action] = norm

    def key_for(self, action: str) -> str | None:
        return self._bindings.get(action)

    def action_for(self, key: str) -> str | None:
        norm = self._normalize(key)
        return next((a for a, k in self._bindings.items() if k == norm), None)

    def conflicts(self) -> list[str]:
        seen: dict[str, str] = {}
        dupes = []
        for action, key in self._bindings.items():
            if key in seen:
                dupes.append(key)
            seen[key] = action
        return dupes

    def to_dict(self) -> dict[str, str]:
        return dict(self._bindings)
