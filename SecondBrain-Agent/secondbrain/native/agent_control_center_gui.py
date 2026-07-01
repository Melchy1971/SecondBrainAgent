from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

from secondbrain.native.agent_control_center import AgentControlCenter


class AgentControlCenterGui(tk.Tk):
    def __init__(self, project_root: str | Path = ".") -> None:
        super().__init__()
        self.project_root = Path(project_root).resolve()
        self.center = AgentControlCenter(self.project_root)
        self.title("Jarvis - Agent Control Center")
        self.geometry("980x640")
        self.configure(bg="#0f172a")
        self._build()
        self.refresh()

    def _build(self) -> None:
        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)
        top = ttk.Frame(root)
        top.pack(fill="x")
        ttk.Label(top, text="Agent Control Center", font=("Segoe UI", 16, "bold")).pack(side="left")
        ttk.Button(top, text="Aktualisieren", command=self.refresh).pack(side="right")

        add = ttk.Frame(root)
        add.pack(fill="x", pady=(12, 8))
        self.task_text = tk.StringVar()
        ttk.Entry(add, textvariable=self.task_text).pack(side="left", fill="x", expand=True)
        ttk.Button(add, text="Aufgabe planen", command=self.plan_task).pack(side="left", padx=4)
        ttk.Button(add, text="Aufgabe anlegen", command=self.add_task).pack(side="left", padx=4)

        panes = ttk.Panedwindow(root, orient="horizontal")
        panes.pack(fill="both", expand=True)

        left = ttk.Frame(panes)
        right = ttk.Frame(panes)
        panes.add(left, weight=2)
        panes.add(right, weight=3)

        ttk.Label(left, text="Agenten").pack(anchor="w")
        self.agent_list = tk.Listbox(left, height=8)
        self.agent_list.pack(fill="x", pady=(0, 8))

        ttk.Label(left, text="Aufgaben").pack(anchor="w")
        self.task_list = tk.Listbox(left)
        self.task_list.pack(fill="both", expand=True)
        self.task_list.bind("<<ListboxSelect>>", lambda _e: self.show_selected_task())

        buttons = ttk.Frame(left)
        buttons.pack(fill="x", pady=8)
        ttk.Button(buttons, text="Ausführen", command=lambda: self.run_selected(False)).pack(side="left", padx=2)
        ttk.Button(buttons, text="Bestätigt ausführen", command=lambda: self.run_selected(True)).pack(side="left", padx=2)
        ttk.Button(buttons, text="Abbrechen", command=self.cancel_selected).pack(side="left", padx=2)

        ttk.Label(right, text="Details / Plan / Audit").pack(anchor="w")
        self.detail = tk.Text(right, wrap="word")
        self.detail.pack(fill="both", expand=True)

    def refresh(self) -> None:
        self.agent_list.delete(0, tk.END)
        for agent in self.center.agents():
            mark = "OK" if agent.get("available") else "FEHLT"
            self.agent_list.insert(tk.END, f"{mark} | {agent['id']} | {agent['name']}")
        self.task_list.delete(0, tk.END)
        for task in self.center.tasks(limit=200):
            approval = " | FREIGABE" if task.get("requires_approval") else ""
            self.task_list.insert(tk.END, f"{task.get('status')} | {task.get('id')} | {task.get('title')}{approval}")
        self._write_detail(self.center.status())

    def _write_detail(self, payload: dict) -> None:
        self.detail.delete("1.0", tk.END)
        self.detail.insert(tk.END, json.dumps(payload, ensure_ascii=False, indent=2))

    def plan_task(self) -> None:
        self._write_detail(self.center.plan(self.task_text.get()))

    def add_task(self) -> None:
        payload = self.center.add_task(self.task_text.get())
        self._write_detail(payload)
        if payload.get("ok"):
            self.task_text.set("")
        self.refresh()

    def _selected_task_id(self) -> str:
        sel = self.task_list.curselection()
        if not sel:
            return ""
        text = self.task_list.get(sel[0])
        parts = [p.strip() for p in text.split("|")]
        return parts[1] if len(parts) > 1 else ""

    def show_selected_task(self) -> None:
        task_id = self._selected_task_id()
        for task in self.center.tasks(limit=500):
            if task.get("id") == task_id:
                self._write_detail(task)
                return

    def run_selected(self, confirmed: bool) -> None:
        task_id = self._selected_task_id()
        if not task_id:
            messagebox.showwarning("Jarvis", "Keine Aufgabe ausgewählt.")
            return
        payload = self.center.run_task(task_id, confirmed=confirmed)
        self._write_detail(payload)
        self.refresh()

    def cancel_selected(self) -> None:
        task_id = self._selected_task_id()
        if not task_id:
            return
        self._write_detail(self.center.cancel_task(task_id))
        self.refresh()


def run_agent_control_center_gui(project_root: str | Path = ".") -> int:
    app = AgentControlCenterGui(project_root)
    app.mainloop()
    return 0
