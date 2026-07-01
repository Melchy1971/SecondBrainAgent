from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from .service import JobQueueService


class JobQueueCenterFrame(ttk.Frame):
    def __init__(self, master: tk.Misc, service: JobQueueService | None = None) -> None:
        super().__init__(master, padding=12)
        self.service = service or JobQueueService()
        self.tree = ttk.Treeview(self, columns=("kind", "status", "priority", "updated"), show="headings", height=16)
        for key, label, width in [("kind", "Typ", 90), ("status", "Status", 110), ("priority", "Prio", 70), ("updated", "Aktualisiert", 180)]:
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width, anchor="w")
        self.tree.pack(fill="both", expand=True)
        buttons = ttk.Frame(self)
        buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(buttons, text="Aktualisieren", command=self.refresh).pack(side="left")
        ttk.Button(buttons, text="Freigeben", command=self.approve_selected).pack(side="left", padx=6)
        ttk.Button(buttons, text="Starten", command=self.run_selected).pack(side="left")
        ttk.Button(buttons, text="Abbrechen", command=self.cancel_selected).pack(side="left", padx=6)
        self.summary = ttk.Label(self, text="")
        self.summary.pack(fill="x", pady=(8, 0))
        self.refresh()

    def selected_id(self) -> str | None:
        selection = self.tree.selection()
        return selection[0] if selection else None

    def refresh(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        snap = self.service.snapshot()
        for job in snap["jobs"]:
            self.tree.insert("", "end", iid=job["id"], values=(job["kind"], job["status"], job["priority"], job["updated_at"]))
        self.summary.config(text=f"Jobs: {snap['total']} | Blockiert: {snap['blocked']} | Laufend: {snap['running']} | Health: {snap['health']}")

    def approve_selected(self) -> None:
        job_id = self.selected_id()
        if not job_id:
            return
        self.service.approve(job_id)
        self.refresh()

    def run_selected(self) -> None:
        job_id = self.selected_id()
        if not job_id:
            return
        self.service.update_status(job_id, "running")
        self.refresh()

    def cancel_selected(self) -> None:
        job_id = self.selected_id()
        if not job_id:
            return
        self.service.cancel(job_id)
        self.refresh()


def launch() -> None:
    root = tk.Tk()
    root.title("Jarvis – Job & Queue Center")
    root.geometry("820x520")
    JobQueueCenterFrame(root).pack(fill="both", expand=True)
    root.mainloop()


if __name__ == "__main__":
    launch()
