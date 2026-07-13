"""Embedded v30.49 task cockpit for the existing AI Workspace shell."""
from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

from secondbrain.gui.agent_plan_viewer import AgentPlanViewer
from .task_workspace import TaskWorkspaceService


class TaskWorkspaceFrame(ttk.Frame):
    def __init__(self, master: tk.Misc, project_root: str | Path):
        super().__init__(master)
        self.service = TaskWorkspaceService(project_root)
        self.query = tk.StringVar()
        self.status = tk.StringVar(value="")
        self.message = tk.StringVar()
        self.plan_viewer = AgentPlanViewer()
        self._build()
        self.reload()

    def _build(self) -> None:
        bar = ttk.Frame(self, padding=6); bar.pack(fill="x")
        ttk.Entry(bar, textvariable=self.query).pack(side="left", fill="x", expand=True)
        ttk.Combobox(bar, textvariable=self.status, values=("", "pending", "running", "done", "failed", "cancelled"), state="readonly", width=12).pack(side="left", padx=4)
        ttk.Button(bar, text="Filtern", command=self.reload).pack(side="left")
        ttk.Button(bar, text="Neue Aufgabe", command=self.add_task).pack(side="left", padx=(12, 2))
        ttk.Button(bar, text="Erinnerung", command=self.add_reminder).pack(side="left", padx=2)
        ttk.Button(bar, text="Kalender", command=self.add_calendar).pack(side="left", padx=2)
        ttk.Button(bar, text="Agent Job", command=self.add_job).pack(side="left", padx=2)
        self.tabs = ttk.Notebook(self); self.tabs.pack(fill="both", expand=True)
        self.task_tree = self._tree("Aufgaben", ("priority", "due", "dependencies", "status"))
        self.reminder_tree = self._tree("Erinnerungen", ("reminder", "priority", "status"))
        self.calendar_tree = self._tree("Kalender", ("due", "priority", "status"))
        self.job_tree = self._tree("Agent Jobs", ("kind", "priority", "status"))
        self.approval_tree = self._tree("Genehmigungen", ("intent", "created", "status"))
        self.plan_tree = self._tree("Plaene", ("status", "steps", "risk", "approval"))
        self.history_tree = self._tree("Historie", ("source", "event", "time"))
        self.plan_detail = tk.Text(self.tabs, wrap="word", height=10)
        self.tabs.add(self.plan_detail, text="Plan Explain")
        actions = ttk.Frame(self); actions.pack(fill="x", pady=4)
        for label, command in (("Ausfuehren", self.run_task), ("Erledigt", self.complete), ("Abbrechen", self.cancel),
                               ("Genehmigen", lambda: self.decide(True)), ("Ablehnen", lambda: self.decide(False))):
            ttk.Button(actions, text=label, command=command).pack(side="left", padx=2)
        ttk.Button(actions, text="Plan erstellen", command=self.add_plan).pack(side="left", padx=(12, 2))
        ttk.Button(actions, text="Plan fortsetzen", command=self.resume_plan).pack(side="left", padx=2)
        ttk.Button(actions, text="Plan erklaeren", command=self.explain_plan).pack(side="left", padx=2)
        ttk.Label(self, textvariable=self.message).pack(fill="x")

    def _tree(self, title, columns):
        frame = ttk.Frame(self.tabs); self.tabs.add(frame, text=title)
        tree = ttk.Treeview(frame, columns=columns, show="tree headings")
        tree.heading("#0", text="Titel")
        for column in columns: tree.heading(column, text=column.title())
        tree.pack(fill="both", expand=True)
        return tree

    @staticmethod
    def _clear(tree):
        for item in tree.get_children(): tree.delete(item)

    def reload(self) -> None:
        payload = self.service.snapshot()
        for tree in (self.task_tree, self.reminder_tree, self.calendar_tree, self.job_tree, self.approval_tree, self.plan_tree, self.history_tree): self._clear(tree)
        for row in self.service.tasks(status=self.status.get() or None, query=self.query.get()):
            self.task_tree.insert("", "end", iid=row["id"], text=row["title"], values=(row.get("priority", 50), row.get("due_at") or "", ", ".join(row.get("dependencies") or ()), row.get("status")))
        for row in payload["reminders"]:
            self.reminder_tree.insert("", "end", iid=row["id"], text=row["title"], values=(row["reminder_at"], row.get("priority", 50), row.get("status")))
        for row in payload["calendar"]:
            self.calendar_tree.insert("", "end", iid=row["id"], text=row["title"], values=(row["due_at"], row.get("priority", 50), row.get("status")))
        for row in payload["jobs"]["jobs"]:
            self.job_tree.insert("", "end", iid=row["id"], text=row["title"], values=(row["kind"], row["priority"], row["status"]))
        for row in payload["approvals"]:
            self.approval_tree.insert("", "end", iid=row["approval_id"], text=row["text"], values=(row["intent"], row["created_at"], row["status"]))
        for row in payload.get("plans", []):
            steps = len(row.get("steps") or [])
            risk = str((row.get("metadata") or {}).get("maximum_risk", "low"))
            approvals = sum(1 for step in row.get("steps") or [] if bool(step.get("requires_approval")))
            self.plan_tree.insert("", "end", iid=row["id"], text=row.get("goal", ""), values=(row.get("status"), steps, risk, approvals))
        for index, row in enumerate(payload["history"]):
            self.history_tree.insert("", "end", iid=f"history-{index}", text=str(row.get("title") or row.get("id") or row.get("event", "Aktivitaet")), values=(row.get("source"), row.get("event", row.get("status")), row.get("ts", row.get("updated_at", ""))))
        summary = payload["summary"]
        self.message.set(f"{summary['open']} offen | {summary['reminders']} Erinnerungen | {summary['agent_jobs']} Jobs | {summary['pending_approvals']} Genehmigungen | {summary.get('plans', 0)} Plaene")

    def _title_priority(self):
        title = simpledialog.askstring("Aufgabe", "Titel", parent=self)
        if not title: return None
        priority = simpledialog.askinteger("Prioritaet", "0 (hoch) bis 100 (niedrig)", initialvalue=50, minvalue=0, maxvalue=100, parent=self)
        return (title, 50 if priority is None else priority)

    def add_task(self):
        value = self._title_priority()
        if value:
            dependency = simpledialog.askstring("Abhaengigkeit", "Optionale Task-ID", parent=self) or ""
            result = self.service.add_task(value[0], priority=value[1], dependencies=[dependency] if dependency else [])
            if not result.get("ok"): messagebox.showerror("Aufgabe", str(result), parent=self)
            self.reload()

    def add_reminder(self):
        value = self._title_priority()
        if value:
            when = simpledialog.askstring("Erinnerung", "Zeitpunkt (ISO 8601)", parent=self)
            if when:
                try: self.service.add_reminder(value[0], when, priority=value[1])
                except ValueError as exc: messagebox.showerror("Erinnerung", str(exc), parent=self)
                self.reload()

    def add_calendar(self):
        value = self._title_priority()
        if value:
            when = simpledialog.askstring("Kalender", "Faelligkeit (ISO 8601)", parent=self)
            if when:
                try: self.service.add_calendar_task(value[0], when, priority=value[1])
                except ValueError as exc: messagebox.showerror("Kalender", str(exc), parent=self)
                self.reload()

    def add_job(self):
        value = self._title_priority()
        if value: self.service.enqueue_agent_job(value[0], priority=value[1]); self.reload()

    def _selected_task(self):
        selected = self.task_tree.selection()
        return selected[0] if selected else None

    def run_task(self):
        task_id = self._selected_task()
        if task_id: self.service.run_task(task_id); self.reload()

    def complete(self):
        task_id = self._selected_task()
        if task_id: self.service.tasks_service.complete_task(task_id); self.reload()

    def cancel(self):
        task_id = self._selected_task()
        if task_id: self.service.tasks_service.cancel_task(task_id); self.reload()

    def decide(self, approved):
        selected = self.approval_tree.selection()
        if selected: self.service.decide_approval(selected[0], approved); self.reload()

    def _selected_plan(self):
        selected = self.plan_tree.selection()
        return selected[0] if selected else None

    def add_plan(self):
        goal = simpledialog.askstring("Plan", "Ziel", parent=self)
        if not goal:
            return
        result = self.service.create_plan(goal)
        if not result.get("ok"):
            messagebox.showerror("Plan", str(result), parent=self)
        self.reload()

    def resume_plan(self):
        plan_id = self._selected_plan()
        if not plan_id:
            return
        result = self.service.resume_plan(plan_id)
        if not result.get("ok"):
            messagebox.showerror("Plan", str(result), parent=self)
        self.reload()

    def explain_plan(self):
        plan_id = self._selected_plan()
        if not plan_id:
            return
        explanation = self.service.explain_plan(plan_id)
        plan = next((row for row in self.service.plans() if row.get("id") == plan_id), None)
        if plan is None:
            return
        view = self.plan_viewer.render(plan, explanation=explanation)
        self.plan_detail.delete("1.0", tk.END)
        self.plan_detail.insert("1.0", json.dumps(view, indent=2, ensure_ascii=False, default=str))
        self.tabs.select(self.plan_detail)
