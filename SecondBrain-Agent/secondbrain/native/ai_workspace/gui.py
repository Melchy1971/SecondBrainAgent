from __future__ import annotations

import json
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from secondbrain.native.layout_center.service import NativeLayoutService
from secondbrain.native.theme_center.service import ThemeCenterService

from .service import AIWorkspaceService


class AIWorkspaceApp(tk.Tk):
    """Integrated native shell for the independently testable desktop centers."""

    def __init__(self, project_root: str | Path = ".") -> None:
        super().__init__()
        self.project_root = Path(project_root).resolve()
        self.service = AIWorkspaceService(self.project_root)
        self.theme_service = ThemeCenterService(self.project_root)
        self.layout_service = NativeLayoutService(self.project_root)
        self.title("Jarvis - Native AI Workspace")
        self.geometry("1240x780")
        self.minsize(960, 620)
        self._build()
        self.refresh()

    def _build(self) -> None:
        theme = self.theme_service.current_theme().tokens
        background = theme.get("background", "#0F172A")
        foreground = theme.get("foreground", "#E5E7EB")
        self.configure(bg=background)
        header = tk.Frame(self, bg=background)
        header.pack(fill="x", padx=14, pady=12)
        tk.Label(header, text="Jarvis AI Workspace", bg=background, fg=foreground, font=("Segoe UI", 20, "bold")).pack(side="left")
        ttk.Button(header, text="Aktualisieren", command=self.refresh).pack(side="right")

        body = tk.PanedWindow(self, orient="horizontal", bg=background, sashwidth=4)
        body.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        navigation = ttk.Frame(body, padding=8)
        content = ttk.Frame(body, padding=8)
        layout = self.layout_service.load()["layout"]
        body.add(navigation, width=layout.get("left_width", 260))
        body.add(content)

        self.navigation = ttk.Treeview(navigation, columns=("status",), show="tree headings")
        self.navigation.heading("#0", text="Modul")
        self.navigation.heading("status", text="Status")
        self.navigation.column("#0", width=180)
        self.navigation.column("status", width=70)
        self.navigation.pack(fill="both", expand=True)
        self.navigation.bind("<Double-1>", self._open_selected)
        self.detail = tk.Text(content, wrap="word")
        self.detail.pack(fill="both", expand=True)

    def refresh(self) -> None:
        self.snapshot = self.service.status()
        for item in self.navigation.get_children():
            self.navigation.delete(item)
        for module in self.snapshot["modules"]:
            self.navigation.insert("", "end", iid=module["id"], text=module["title"], values=(module["status"],))
        self._show(self.snapshot)

    def _open_selected(self, _event: object | None = None) -> None:
        selected = self.navigation.selection()
        if not selected:
            return
        module = next((item for item in self.snapshot["modules"] if item["id"] == selected[0]), None)
        if module is None or module["status"] != "ready":
            return
        result = subprocess.run(
            [sys.executable, str(self.project_root / "launcher.py"), module["command"], "--project-root", str(self.project_root)],
            cwd=self.project_root, text=True, capture_output=True, timeout=30, check=False,
        )
        self.service.record_activity("module_opened", {"module": module["id"], "returncode": result.returncode})
        self._show({"module": module, "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr})

    def _show(self, payload: object) -> None:
        self.detail.delete("1.0", "end")
        self.detail.insert("1.0", json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def run_gui(project_root: str | Path = ".") -> int:
    app = AIWorkspaceApp(project_root)
    app.mainloop()
    return 0
