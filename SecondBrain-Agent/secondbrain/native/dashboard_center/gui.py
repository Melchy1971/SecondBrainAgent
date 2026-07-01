from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk

from .service import NativeDashboardService


class DashboardCenterApp(tk.Tk):
    def __init__(self, project_root: str | Path = ".") -> None:
        super().__init__()
        self.project_root = Path(project_root)
        self.service = NativeDashboardService(self.project_root)
        self.title("Jarvis – Native Dashboard Center")
        self.geometry("1180x720")
        self.configure(bg="#0F172A")
        self._build()
        self.refresh()

    def _build(self) -> None:
        header = tk.Frame(self, bg="#0F172A")
        header.pack(fill="x", padx=14, pady=12)
        tk.Label(header, text="Dashboard", fg="#E5E7EB", bg="#0F172A", font=("Segoe UI", 20, "bold")).pack(side="left")
        ttk.Button(header, text="Aktualisieren", command=self.refresh).pack(side="right")

        body = tk.PanedWindow(self, orient="horizontal", bg="#0F172A", sashwidth=4)
        body.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        left = tk.Frame(body, bg="#111827")
        right = tk.Frame(body, bg="#020617")
        body.add(left, width=760)
        body.add(right)

        self.tree = ttk.Treeview(left, columns=("status", "value", "command"), show="tree headings")
        self.tree.heading("#0", text="Bereich")
        self.tree.heading("status", text="Status")
        self.tree.heading("value", text="Wert")
        self.tree.heading("command", text="Aktion")
        self.tree.column("#0", width=220)
        self.tree.column("status", width=90)
        self.tree.column("value", width=180)
        self.tree.column("command", width=180)
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        self.tree.bind("<<TreeviewSelect>>", self.show_selected)

        self.detail = tk.Text(right, bg="#020617", fg="#E5E7EB", insertbackground="#E5E7EB", wrap="word")
        self.detail.pack(fill="both", expand=True, padx=8, pady=8)

    def refresh(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.snapshot = self.service.snapshot().to_dict()
        for card in self.snapshot["cards"]:
            value = card["value"]
            if isinstance(value, dict):
                value = ", ".join(f"{k}={v}" for k, v in value.items())
            self.tree.insert("", "end", iid=card["id"], text=card["title"], values=(card["status"], str(value), card.get("command") or ""))
        self.show_payload(self.snapshot)

    def show_payload(self, payload: dict) -> None:
        import json

        self.detail.delete("1.0", "end")
        self.detail.insert("end", json.dumps(payload, indent=2, ensure_ascii=False, default=str))

    def show_selected(self, _event=None) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        card_id = selected[0]
        for card in self.snapshot.get("cards", []):
            if card.get("id") == card_id:
                self.show_payload(card)
                return


def run_gui(project_root: str | Path = ".") -> None:
    app = DashboardCenterApp(project_root)
    app.mainloop()
