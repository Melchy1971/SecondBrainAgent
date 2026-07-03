from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Any

from secondbrain.native.layout_center.service import NativeLayoutService
from secondbrain.native.theme_center.service import ThemeCenterService

from .models import ApplicationState
from .service import AIWorkspaceService


class AIWorkspaceApp(tk.Tk):
    """Shared native shell for all desktop modules."""

    def __init__(self, project_root: str | Path = ".") -> None:
        super().__init__()
        self.project_root = Path(project_root).resolve()
        self.service = AIWorkspaceService(self.project_root)
        self.theme_service = ThemeCenterService(self.project_root)
        self.layout_service = NativeLayoutService(self.project_root)
        self.state: ApplicationState = self.service.application_state()
        self.title("Jarvis - Native Desktop")
        self.geometry("1240x780")
        self.minsize(960, 620)
        self._build_shell()
        self.refresh()

    def _build_shell(self) -> None:
        theme = self.theme_service.current_theme().tokens
        background = theme.get("background", "#0F172A")
        foreground = theme.get("foreground", "#E5E7EB")
        self.configure(bg=background)

        header = tk.Frame(self, bg=background)
        header.pack(fill="x", padx=14, pady=(12, 6))
        tk.Label(
            header,
            text="Jarvis Native Desktop",
            bg=background,
            fg=foreground,
            font=("Segoe UI", 20, "bold"),
        ).pack(side="left")
        self.version_label = tk.Label(header, bg=background, fg=foreground)
        self.version_label.pack(side="left", padx=14)

        self.toolbar = ttk.Frame(self, padding=(14, 4))
        self.toolbar.pack(fill="x")
        ttk.Button(self.toolbar, text="Dashboard", command=lambda: self.navigate("dashboard")).pack(side="left")
        ttk.Button(self.toolbar, text="Zurueck", command=self.navigate_back).pack(side="left", padx=6)
        ttk.Button(self.toolbar, text="Aktualisieren", command=self.refresh).pack(side="left")
        self.module_title = ttk.Label(self.toolbar, text="", font=("Segoe UI", 11, "bold"))
        self.module_title.pack(side="right")

        layout = self.layout_service.load()["layout"]
        body = tk.PanedWindow(self, orient="horizontal", bg=background, sashwidth=4)
        body.pack(fill="both", expand=True, padx=14, pady=8)
        navigation_frame = ttk.Frame(body, padding=8)
        content_frame = ttk.Frame(body, padding=8)
        body.add(navigation_frame, width=layout.get("left_width", 260))
        body.add(content_frame)

        self.navigation = ttk.Treeview(navigation_frame, columns=("status",), show="tree headings", selectmode="browse")
        self.navigation.heading("#0", text="Modul")
        self.navigation.heading("status", text="Status")
        self.navigation.column("#0", width=185)
        self.navigation.column("status", width=70, anchor="center")
        self.navigation.pack(fill="both", expand=True)
        self.navigation.bind("<<TreeviewSelect>>", self._on_navigation)

        self.detail = tk.Text(content_frame, wrap="word", borderwidth=0)
        self.detail.pack(fill="both", expand=True)

        self.status_text = tk.StringVar(value="Desktop wird initialisiert")
        self.statusbar = ttk.Label(self, textvariable=self.status_text, relief="sunken", anchor="w", padding=(8, 4))
        self.statusbar.pack(fill="x", side="bottom")

    def refresh(self) -> None:
        snapshot = self.service.snapshot()
        self.state.version = snapshot.version
        self.state.replace_modules(snapshot.modules)
        self.version_label.configure(text=self.state.version)
        current_selection = self.state.active_module
        for item in self.navigation.get_children():
            self.navigation.delete(item)
        for module in self.state.modules:
            self.navigation.insert("", "end", iid=module.id, text=module.title, values=(module.status,))
        if current_selection and self.navigation.exists(current_selection):
            self.navigation.selection_set(current_selection)
            self.navigation.focus(current_selection)
        self._render_active_module()

    def navigate(self, module_id: str) -> None:
        try:
            self.state.select_module(module_id)
        except (KeyError, ValueError) as exc:
            self.state.set_error(str(exc))
            self._update_status()
            return
        if self.navigation.exists(module_id):
            self.navigation.selection_set(module_id)
            self.navigation.focus(module_id)
        self._render_active_module()

    def navigate_back(self) -> None:
        self.navigate("dashboard")

    def _on_navigation(self, _event: object | None = None) -> None:
        selected = self.navigation.selection()
        if selected and selected[0] != self.state.active_module:
            self.navigate(selected[0])

    def _render_active_module(self) -> None:
        module = next((item for item in self.state.modules if item.id == self.state.active_module), None)
        if module is None:
            self._show({"ok": False, "status": "no_active_module"})
            self._update_status()
            return
        payload = self.service.module_payload(module.id)
        if payload.get("status") == "module_error":
            self.state.set_error(f"{module.title}: {payload.get('status', 'Fehler')}")
        elif not payload.get("ok", False):
            self.state.status = "degraded"
            self.state.message = f"{module.title} eingeschraenkt"
            self.state.touch()
        else:
            self.state.status = "ready"
            self.state.message = f"{module.title} bereit"
            self.state.touch()
        self.module_title.configure(text=module.title)
        self._show({"module": module.to_dict(), "data": payload})
        self._update_status()

    def _update_status(self) -> None:
        self.status_text.set(
            f"{self.state.status.upper()} | {self.state.message} | Projekt: {self.state.project_root}"
        )

    def _show(self, payload: Any) -> None:
        self.detail.configure(state="normal")
        self.detail.delete("1.0", "end")
        self.detail.insert("1.0", json.dumps(payload, indent=2, ensure_ascii=False, default=str))
        self.detail.configure(state="disabled")


def run_gui(project_root: str | Path = ".") -> int:
    app = AIWorkspaceApp(project_root)
    app.mainloop()
    return 0
