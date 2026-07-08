from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from .service import NotificationCenterService


class NotificationCenterWindow(tk.Tk):
    def __init__(self, project_root: str | Path = ".") -> None:
        super().__init__()
        self.service = NotificationCenterService(project_root)
        self.title("Jarvis - Benachrichtigungen")
        self.geometry("980x620")
        self.configure(bg="#10131a")
        self._build()
        self.refresh()

    def _build(self) -> None:
        header = tk.Frame(self, bg="#10131a")
        header.pack(fill="x", padx=16, pady=12)
        tk.Label(header, text="Benachrichtigungen", fg="#e8edf5", bg="#10131a", font=("Segoe UI", 18, "bold")).pack(side="left")
        ttk.Button(header, text="Aktualisieren", command=self.refresh).pack(side="right", padx=4)
        ttk.Button(header, text="Alle gelesen", command=self.mark_all_read).pack(side="right", padx=4)
        ttk.Button(header, text="Test senden", command=self.send_test).pack(side="right", padx=4)

        self.summary_var = tk.StringVar(value="")
        tk.Label(self, textvariable=self.summary_var, fg="#9fb3c8", bg="#10131a", anchor="w").pack(fill="x", padx=16)

        columns = ("ts", "level", "category", "title", "read", "action")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=18)
        for column, title, width in [
            ("ts", "Zeit", 160), ("level", "Level", 100), ("category", "Kategorie", 120),
            ("title", "Titel", 300), ("read", "Gelesen", 80), ("action", "Aktion", 90)
        ]:
            self.tree.heading(column, text=title)
            self.tree.column(column, width=width, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=16, pady=10)
        self.tree.bind("<<TreeviewSelect>>", self._select)

        self.detail = tk.Text(self, height=7, bg="#151a22", fg="#e8edf5", insertbackground="#e8edf5", wrap="word")
        self.detail.pack(fill="x", padx=16, pady=(0, 12))

    def refresh(self) -> None:
        status = self.service.status()
        self.summary_var.set(f"Gesamt: {status['total']} | Ungelesen: {status['unread']} | Aktion erforderlich: {status['action_required']}")
        for row in self.tree.get_children():
            self.tree.delete(row)
        for item in self.service.list_items(limit=100).get("items", []):
            self.tree.insert("", "end", iid=item["id"], values=(
                item["ts"], item["level"], item["category"], item["title"], "ja" if item["read"] else "nein", "ja" if item["action_required"] else "nein"
            ))

    def _select(self, _event: object) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        item_id = selection[0]
        items = self.service.list_items(limit=1000).get("items", [])
        selected = next((item for item in items if item["id"] == item_id), None)
        if selected:
            self.detail.delete("1.0", "end")
            self.detail.insert("end", f"{selected['title']}\n\n{selected['message']}\n\nQuelle: {selected['source']}\nAktionen: {', '.join(selected['actions']) if selected['actions'] else '-'}")

    def mark_all_read(self) -> None:
        self.service.mark_all_read()
        self.refresh()

    def send_test(self) -> None:
        self.service.notify("Jarvis Test", "Benachrichtigungssystem ist aktiv.", level="success", category="system", source="notification_center")
        self.refresh()
        messagebox.showinfo("Jarvis", "Testbenachrichtigung gespeichert.")


def run(project_root: str | Path = ".") -> None:
    app = NotificationCenterWindow(project_root)
    app.mainloop()
