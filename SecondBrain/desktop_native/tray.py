from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec
from typing import Callable


@dataclass(frozen=True, slots=True)
class TrayStatus:
    available: bool
    running: bool
    degraded_reason: str = ""


class SystemTrayController:
    def __init__(
        self,
        *,
        on_open: Callable[[], None],
        on_toggle_mute: Callable[[], None],
        on_push_to_talk: Callable[[], None],
        on_exit: Callable[[], None],
        status_text: Callable[[], str],
    ) -> None:
        self.on_open = on_open
        self.on_toggle_mute = on_toggle_mute
        self.on_push_to_talk = on_push_to_talk
        self.on_exit = on_exit
        self.status_text = status_text
        self._icon = None

    @property
    def available(self) -> bool:
        return find_spec("pystray") is not None and find_spec("PIL") is not None

    @property
    def running(self) -> bool:
        return self._icon is not None

    def start(self) -> TrayStatus:
        if self.running:
            return self.status()
        if not self.available:
            return TrayStatus(False, False, "pystray/Pillow nicht installiert")
        import pystray
        from PIL import Image, ImageDraw

        image = Image.new("RGB", (64, 64), "#02060b")
        draw = ImageDraw.Draw(image)
        draw.ellipse((10, 10, 54, 54), outline="#2fe6ff", width=5)
        draw.ellipse((27, 27, 37, 37), fill="#2fe6ff")
        menu = pystray.Menu(
            pystray.MenuItem("Jarvis öffnen", lambda _icon, _item: self.on_open(), default=True),
            pystray.MenuItem(lambda _item: self.status_text(), None, enabled=False),
            pystray.MenuItem("Mikrofon stummschalten", lambda _icon, _item: self.on_toggle_mute()),
            pystray.MenuItem("Push-to-Talk", lambda _icon, _item: self.on_push_to_talk()),
            pystray.MenuItem("Beenden", lambda _icon, _item: self.on_exit()),
        )
        self._icon = pystray.Icon("jarvis-secondbrain", image, "Jarvis SecondBrain", menu)
        self._icon.run_detached()
        return self.status()

    def stop(self) -> None:
        icon, self._icon = self._icon, None
        if icon is not None:
            icon.stop()

    def status(self) -> TrayStatus:
        return TrayStatus(self.available, self.running, "" if self.available else "pystray/Pillow nicht installiert")
