from __future__ import annotations

import re
from importlib.util import find_spec
from typing import Any, Callable


_HOTKEY = re.compile(r"^(?:<(?:ctrl|ctrl_l|ctrl_r|alt|alt_l|alt_r|shift|shift_l|shift_r|cmd)>\+){1,3}[a-z0-9]$")


class GlobalPushToTalkHotkey:
    """Optional global hotkey. It observes only the configured chord, never raw keys."""

    def __init__(
        self,
        callback: Callable[[], None],
        *,
        hotkey: str = "<ctrl>+<alt>+j",
        enabled: bool = False,
        listener_factory: Callable[[dict[str, Callable[[], None]]], Any] | None = None,
    ) -> None:
        normalized = hotkey.casefold().strip()
        if not _HOTKEY.fullmatch(normalized):
            raise ValueError(f"Ungültiger globaler Hotkey: {hotkey}")
        self.callback = callback
        self.hotkey = normalized
        self.enabled = bool(enabled)
        self._listener_factory = listener_factory
        self._listener: Any = None
        self.activations = 0
        self.last_error: str | None = None

    @property
    def available(self) -> bool:
        return self._listener_factory is not None or find_spec("pynput") is not None

    @property
    def running(self) -> bool:
        return self._listener is not None

    def start(self) -> bool:
        if not self.enabled or self.running or not self.available:
            return False
        factory = self._listener_factory
        if factory is None:
            from pynput.keyboard import GlobalHotKeys

            factory = GlobalHotKeys
        try:
            listener = factory({self.hotkey: self._activate})
            listener.start()
        except Exception as exc:
            self.last_error = str(exc)
            return False
        self._listener = listener
        self.last_error = None
        return True

    def stop(self) -> None:
        listener, self._listener = self._listener, None
        if listener is not None:
            listener.stop()

    def status(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "available": self.available,
            "running": self.running,
            "hotkey": self.hotkey,
            "activations": self.activations,
            "last_error": self.last_error,
            "raw_keys_recorded": False,
        }

    def _activate(self) -> None:
        self.activations += 1
        self.callback()
