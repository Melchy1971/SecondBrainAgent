"""Unified application shell (Tkinter) — v30.68.

WARNING: Windows/desktop GUI. NOT executed/verified in the sandbox (no display).
tkinter is imported lazily. All design/interaction LOGIC (secondbrain.ui.*) is
unit-tested; only widget wiring is unverified here.

Goal: give every window the same chrome (nav sidebar, status bar, theming, keyboard
nav, responsive layout) WITHOUT removing any existing functionality. Existing centers
mount into the content area; the shell only standardizes the frame around them.
"""

from __future__ import annotations

from typing import Any, Callable

from secondbrain.ui.theme import ThemeRegistry, ttk_style_map
from secondbrain.ui.keymap import Keymap
from secondbrain.ui.responsive import layout_for
from secondbrain.ui.status_bar import StatusBarModel
from secondbrain.ui.states import ViewState
from secondbrain.ui.workspace_selector import WorkspaceSelectorModel
from secondbrain.ui.activity_feed import ActivityFeedModel
from secondbrain.ui import tokens


class UnifiedShell:
    def __init__(self, master=None, *, title: str = "SecondBrain", theme: str = "dark") -> None:
        import tkinter as tk
        from tkinter import ttk
        self.tk, self.ttk = tk, ttk
        self.root = master or tk.Tk()
        self.themes = ThemeRegistry(theme)
        self.keymap = Keymap()
        self.status = StatusBarModel()
        self.workspaces = WorkspaceSelectorModel()
        self.activity = ActivityFeedModel()
        self.view = ViewState()
        self._panels: dict[str, Callable[[Any], Any]] = {}
        self._build()

    # ---- layout (GUI) -----------------------------------------------------
    def _build(self) -> None:  # pragma: no cover - GUI
        tk, ttk = self.tk, self.ttk
        self.root.title("SecondBrain")
        self.style = ttk.Style(self.root)
        self.apply_theme()
        self.container = ttk.Frame(self.root); self.container.pack(fill=tk.BOTH, expand=True)
        self.sidebar = ttk.Frame(self.container, width=220)
        self.content = ttk.Frame(self.container, style="Surface.TFrame")
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.statusbar = ttk.Frame(self.root, style="Surface.TFrame")
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        self._render_status()
        self._bind_keys()
        self.root.bind("<Configure>", self._on_resize)

    def apply_theme(self) -> None:  # pragma: no cover - GUI
        theme = self.themes.active()
        for style_name, cfg in ttk_style_map(theme).items():
            if style_name != "focus":
                try:
                    self.style.configure(style_name, **cfg)
                except Exception:
                    pass
        try:
            self.root.configure(bg=theme.color("bg"))
        except Exception:
            pass

    def toggle_theme(self) -> None:  # pragma: no cover - GUI
        self.themes.toggle(); self.apply_theme()

    def _render_status(self) -> None:  # pragma: no cover - GUI
        for child in self.statusbar.winfo_children():
            child.destroy()
        theme = self.themes.active()
        for seg in self.status.segments():
            color = theme.palette.get(seg["role"], theme.color("fg_muted"))
            lbl = self.ttk.Label(self.statusbar, text=seg["text"], style="Status.TLabel")
            try:
                lbl.configure(foreground=color)
            except Exception:
                pass
            lbl.pack(side=self.tk.LEFT, padx=tokens.SPACING["sm"])

    def _bind_keys(self) -> None:  # pragma: no cover - GUI
        mapping = {"toggle_theme": self.toggle_theme, "close_window": self.root.destroy}
        for action, handler in mapping.items():
            key = self.keymap.key_for(action)
            if key:
                self.root.bind(_to_tk_sequence(key), lambda e, h=handler: h())

    def _on_resize(self, event) -> None:  # pragma: no cover - GUI
        layout = layout_for(self.root.winfo_width())
        if layout.sidebar == "collapsed":
            self.sidebar.pack_forget()
        elif not self.sidebar.winfo_ismapped():
            self.sidebar.pack(side=self.tk.LEFT, fill=self.tk.Y, before=self.content)

    # ---- panel registration (logic-facing, testable) ---------------------
    def register_panel(self, name: str, factory: Callable[[Any], Any]) -> None:
        self._panels[name] = factory

    def panels(self) -> list[str]:
        return list(self._panels)

    def run(self) -> None:  # pragma: no cover - GUI event loop
        self.root.mainloop()


def _to_tk_sequence(key: str) -> str:
    parts = key.split("+")
    mods = {"Ctrl": "Control", "Alt": "Alt", "Shift": "Shift"}
    seq = "".join(f"<{mods[p]}-" if p in mods else p for p in parts)
    # simplistic mapping; the real binding is refined on the target platform
    return "<" + "-".join(mods.get(p, p) for p in parts) + ">"
