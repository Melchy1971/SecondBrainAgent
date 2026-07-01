from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Any

from secondbrain.native.workspace_center import NativeWorkspaceCenter


class NativeWorkspaceCenterGui:
    """Small native Tkinter workspace shell for Jarvis v30.30."""

    def __init__(self, project_root: str | Path | None = None):
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.center = NativeWorkspaceCenter(self.project_root)
        self.model = self.center.status()
        self.root = tk.Tk()
        self.root.title("Jarvis Workspace Center")
        self.root.geometry("1280x820")
        self.root.minsize(1080, 700)
        self.tabs: ttk.Notebook | None = None
        self._build()

    def run(self) -> int:
        self.root.mainloop()
        return 0

    def refresh(self) -> None:
        self.model = self.center.status()
        if self.tabs is not None:
            self.tabs.destroy()
        self._build_tabs()

    def _build(self) -> None:
        header = ttk.Frame(self.root, padding=12)
        header.pack(fill="x")
        ttk.Label(header, text="Jarvis Workspace Center", font=("Segoe UI", 18, "bold")).pack(side="left")
        ttk.Label(header, text="v30.30 · native · deutsch", font=("Segoe UI", 10)).pack(side="left", padx=16)
        ttk.Button(header, text="Aktualisieren", command=self.refresh).pack(side="right")
        self.status_var = tk.StringVar(value=self._status_line())
        ttk.Label(self.root, textvariable=self.status_var, padding=(12, 4)).pack(fill="x")
        self._build_tabs()

    def _build_tabs(self) -> None:
        self.status_var.set(self._status_line())
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=12)
        self._add_overview_tab()
        for section in self.model.get("sections", []):
            if section.get("id") == "dashboard":
                continue
            self._add_payload_tab(section.get("title", section.get("id", "Bereich")), self._payload_for(section.get("id", "")))

    def _status_line(self) -> str:
        runtime = self.model.get("runtime", {})
        return " | ".join([
            f"Status: {self.model.get('status', 'unknown')}",
            f"Bootstrap: {runtime.get('bootstrap_status', 'unknown')}",
            f"RAG: {runtime.get('rag_status', 'unknown')}",
            f"Provider: {runtime.get('embedding_provider', 'unknown')}",
            f"Projekt: {self.project_root}",
        ])

    def _add_overview_tab(self) -> None:
        frame = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(frame, text="Dashboard")
        cards = ttk.Frame(frame)
        cards.pack(fill="x", pady=(0, 10))
        values = [
            ("Modus", self.model.get("primary_surface")),
            ("Sektionen", self.model.get("section_count")),
            ("Chat", self.model.get("chat", {}).get("total_messages", 0)),
            ("Aktivitäten", self.model.get("activity", {}).get("total_activities", 0)),
            ("Web-HUD", self.model.get("web_hud")),
        ]
        for title, value in values:
            box = ttk.LabelFrame(cards, text=title, padding=10)
            box.pack(side="left", fill="x", expand=True, padx=4)
            ttk.Label(box, text=str(value), font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self._json(frame, self.model)

    def _add_payload_tab(self, title: str, payload: Any) -> None:
        frame = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(frame, text=title)
        ttk.Label(frame, text=title, font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))
        self._json(frame, payload)

    def _payload_for(self, section_id: str) -> Any:
        mapping = {
            "chat": self.model.get("chat"),
            "documents": self.model.get("documents"),
            "search": self.model.get("search"),
            "memory": self.model.get("memory"),
            "tasks": self.model.get("tasks"),
            "agents": self.model.get("agents"),
            "activity": self.model.get("activity"),
            "settings": {"project_root": self.model.get("project_root"), "runtime": self.model.get("runtime")},
            "developer": self.model,
        }
        return mapping.get(section_id, {})

    def _json(self, parent: tk.Widget, payload: Any) -> tk.Text:
        text = tk.Text(parent, wrap="word")
        text.insert("1.0", json.dumps(payload, indent=2, ensure_ascii=False, default=str))
        text.configure(state="disabled")
        text.pack(fill="both", expand=True)
        return text


def run_workspace_center_gui(project_root: str | Path | None = None) -> int:
    return NativeWorkspaceCenterGui(project_root).run()
