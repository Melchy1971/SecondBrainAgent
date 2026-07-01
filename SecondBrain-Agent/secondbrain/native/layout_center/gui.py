from __future__ import annotations

import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk

from .service import NativeLayoutService


class LayoutCenterApp(tk.Tk):
    def __init__(self, project_root: str | Path = ".") -> None:
        super().__init__()
        self.project_root = Path(project_root)
        self.service = NativeLayoutService(self.project_root)
        self.title("Jarvis – Native Docking Layout")
        self.geometry("1200x760")
        self.configure(bg="#0F172A")
        self._build()
        self.refresh()

    def _build(self) -> None:
        header = tk.Frame(self, bg="#0F172A")
        header.pack(fill="x", padx=14, pady=12)
        tk.Label(header, text="Docking Layout", fg="#E5E7EB", bg="#0F172A", font=("Segoe UI", 20, "bold")).pack(side="left")
        ttk.Button(header, text="Aktualisieren", command=self.refresh).pack(side="right")
        ttk.Button(header, text="Standard wiederherstellen", command=self.reset_defaults).pack(side="right", padx=(0, 8))

        body = tk.PanedWindow(self, orient="horizontal", bg="#0F172A", sashwidth=4)
        body.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        left = tk.Frame(body, bg="#111827")
        center = tk.Frame(body, bg="#020617")
        right = tk.Frame(body, bg="#111827")
        body.add(left, width=340)
        body.add(center, width=520)
        body.add(right)

        self.layouts = ttk.Treeview(left, columns=("title", "panels"), show="tree headings")
        self.layouts.heading("#0", text="Name")
        self.layouts.heading("title", text="Titel")
        self.layouts.heading("panels", text="Panels")
        self.layouts.column("#0", width=120)
        self.layouts.column("title", width=150)
        self.layouts.column("panels", width=70)
        self.layouts.pack(fill="both", expand=True, padx=8, pady=8)
        self.layouts.bind("<<TreeviewSelect>>", self.show_selected)

        controls = tk.Frame(left, bg="#111827")
        controls.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(controls, text="Aktivieren", command=self.activate_selected).pack(side="left")
        ttk.Button(controls, text="Export", command=self.export_selected).pack(side="left", padx=6)

        self.preview = tk.Text(center, bg="#020617", fg="#E5E7EB", insertbackground="#E5E7EB", wrap="word")
        self.preview.pack(fill="both", expand=True, padx=8, pady=8)

        tk.Label(right, text="Panels", fg="#E5E7EB", bg="#111827", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=8, pady=(8, 2))
        self.panels = ttk.Treeview(right, columns=("region", "visible", "command"), show="tree headings")
        self.panels.heading("#0", text="Panel")
        self.panels.heading("region", text="Region")
        self.panels.heading("visible", text="Sichtbar")
        self.panels.heading("command", text="Kommando")
        self.panels.pack(fill="both", expand=True, padx=8, pady=8)

    def refresh(self) -> None:
        for row in self.layouts.get_children():
            self.layouts.delete(row)
        self.payload = self.service.list_layouts()
        active = self.payload.get("active")
        for layout in self.payload.get("layouts", []):
            name = layout.get("name")
            title = layout.get("title")
            label = f"{name} *" if name == active else str(name)
            self.layouts.insert("", "end", iid=str(name), text=label, values=(title, len(layout.get("panels", []))))
        self.show_payload(self.service.status())

    def selected_name(self) -> str | None:
        selected = self.layouts.selection()
        return selected[0] if selected else None

    def show_payload(self, payload: dict) -> None:
        self.preview.delete("1.0", "end")
        self.preview.insert("end", json.dumps(payload, indent=2, ensure_ascii=False, default=str))

    def show_selected(self, _event=None) -> None:
        name = self.selected_name()
        if not name:
            return
        payload = self.service.load(name)
        self.show_payload(payload)
        for row in self.panels.get_children():
            self.panels.delete(row)
        for panel in payload.get("layout", {}).get("panels", []):
            self.panels.insert("", "end", text=panel.get("title"), values=(panel.get("region"), panel.get("visible"), panel.get("command") or ""))

    def activate_selected(self) -> None:
        name = self.selected_name()
        if name:
            self.show_payload(self.service.activate(name))
            self.refresh()

    def export_selected(self) -> None:
        name = self.selected_name()
        if name:
            self.show_payload(self.service.export(name))

    def reset_defaults(self) -> None:
        self.show_payload(self.service.reset())
        self.refresh()


def run_gui(project_root: str | Path = ".") -> None:
    app = LayoutCenterApp(project_root)
    app.mainloop()
