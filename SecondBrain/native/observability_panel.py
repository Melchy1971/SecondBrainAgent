"""GUI Audit Viewer: Health, letzte kritische Events, Fehlergruppen, JSON-Export.

MITTE-Zone der Desktop-Shell; liest ausschließlich über ObservabilityService.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from secondbrain.observability import ObservabilityService

FONT = "Segoe UI"


class ObservabilityFrame(ttk.Frame):
    def __init__(self, master: tk.Misc, project_root: str | Path = ".") -> None:
        super().__init__(master, padding=8)
        self.service = ObservabilityService(project_root)

        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 6))
        ttk.Label(top, text="Audit Viewer — Health, Events, Fehlergruppen",
                  font=(FONT, 12, "bold")).pack(side="left")
        ttk.Button(top, text="Neu laden", command=self.reload).pack(side="right", padx=(4, 0))
        ttk.Button(top, text="Export als JSON", command=self.export_json).pack(side="right")

        self.health_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.health_var, font=(FONT, 10, "bold")).pack(fill="x")
        self.export_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.export_var, font=(FONT, 8)).pack(fill="x")

        filters = ttk.Frame(self)
        filters.pack(fill="x", pady=6)
        ttk.Label(filters, text="Actor:").pack(side="left")
        self.actor_var = tk.StringVar(value="")
        ttk.Entry(filters, textvariable=self.actor_var, width=18).pack(side="left", padx=(2, 10))
        ttk.Label(filters, text="Status:").pack(side="left")
        self.status_var = tk.StringVar(value="")
        ttk.Combobox(filters, textvariable=self.status_var, width=10, state="readonly",
                     values=("", "ok", "failed", "denied", "pending")).pack(side="left", padx=(2, 10))
        ttk.Button(filters, text="Filtern", command=self.reload).pack(side="left")

        columns = ("ts", "actor", "action", "resource", "status", "kategorie", "correlation")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=14)
        widths = (150, 90, 170, 170, 70, 90, 150)
        for column, width in zip(columns, widths):
            self.tree.heading(column, text=column.capitalize())
            self.tree.column(column, width=width, stretch=column in ("action", "resource"))
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")

        right = ttk.Frame(self, padding=(8, 0, 0, 0))
        right.pack(side="left", fill="both")
        ttk.Label(right, text="Fehler nach Ursache", font=(FONT, 10, "bold")).pack(anchor="w")
        self.groups_text = tk.Text(right, width=34, height=10, wrap="word", borderwidth=0)
        self.groups_text.pack(fill="y", expand=True)

        self.reload()

    def reload(self) -> None:
        snapshot = self.service.snapshot(limit=200)
        health = snapshot["health"]
        components = ", ".join(
            f"{name}={data['status']}" for name, data in health.get("components", {}).items())
        self.health_var.set(f"Health: {health.get('overall', 'unknown').upper()}"
                            + (f"  ({components})" if components else ""))

        for item in self.tree.get_children():
            self.tree.delete(item)
        events = self.service.audit.query(
            actor=self.actor_var.get() or None,
            status=self.status_var.get() or None,
            limit=200,
        )
        for event in reversed(events):
            self.tree.insert("", "end", values=(
                str(event.get("ts", ""))[:19],
                event.get("actor", ""),
                event.get("action", ""),
                event.get("resource", ""),
                event.get("status", ""),
                event.get("category", ""),
                event.get("correlation_id", ""),
            ))

        groups = snapshot["error_groups"]
        self.groups_text.configure(state="normal")
        self.groups_text.delete("1.0", "end")
        lines = [f"gesamt: {groups.get('total', 0)}"]
        for category, count in groups.get("by_category", {}).items():
            lines.append(f"  {category}: {count}")
        critical = snapshot.get("critical_events", [])
        if critical:
            lines.append("")
            lines.append("Letzte kritische Events:")
            for event in critical[-5:]:
                lines.append(f"  {str(event.get('ts', ''))[:19]} {event.get('action', '')}")
        self.groups_text.insert("1.0", "\n".join(lines))
        self.groups_text.configure(state="disabled")

    def export_json(self) -> None:
        target = self.service.export_json()
        self.export_var.set(f"exportiert: {target}")


class ObservabilityWorkspaceFrame(ObservabilityFrame):
    """Namenskonvention der übrigen Workspace-Panels."""
