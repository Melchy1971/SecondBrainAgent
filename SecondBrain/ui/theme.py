"""Theme resolution (light/dark) + ttk style map as pure data."""

from __future__ import annotations

from dataclasses import dataclass

from secondbrain.ui import tokens


@dataclass(frozen=True)
class Theme:
    name: str
    palette: dict

    def color(self, role: str) -> str:
        return self.palette[role]


class ThemeRegistry:
    def __init__(self, default: str = "dark") -> None:
        self._themes = {name: Theme(name, tokens.palette(name)) for name in tokens.PALETTES}
        self.current = default if default in self._themes else "dark"

    def get(self, name: str) -> Theme:
        return self._themes[name]

    def active(self) -> Theme:
        return self._themes[self.current]

    def toggle(self) -> Theme:
        self.current = "light" if self.current == "dark" else "dark"
        return self.active()

    def set(self, name: str) -> Theme:
        if name not in self._themes:
            raise ValueError(f"unknown theme: {name}")
        self.current = name
        return self.active()


def ttk_style_map(theme: Theme) -> dict:
    """Data-only style map a Tkinter/ttk layer can apply (keeps GUI code thin)."""
    p = theme.palette
    return {
        "TFrame": {"background": p["bg"]},
        "Surface.TFrame": {"background": p["surface"]},
        "TLabel": {"background": p["bg"], "foreground": p["fg"]},
        "Muted.TLabel": {"background": p["bg"], "foreground": p["fg_muted"]},
        "TButton": {"background": p["surface_alt"], "foreground": p["fg"], "borderwidth": 0,
                    "padding": (tokens.SPACING["md"], tokens.SPACING["sm"])},
        "Primary.TButton": {"background": p["primary"], "foreground": p["on_primary"],
                            "padding": (tokens.SPACING["md"], tokens.SPACING["sm"])},
        "Status.TLabel": {"background": p["surface"], "foreground": p["fg_muted"]},
        "focus": {"highlightcolor": p["focus"], "highlightthickness": 2},
    }
