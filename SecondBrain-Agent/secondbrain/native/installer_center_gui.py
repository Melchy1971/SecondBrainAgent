from __future__ import annotations

import json
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from .installer_center import installer_status, installer_plan, write_installer_artifacts


class InstallerCenterGui(tk.Tk):
    def __init__(self, project_root: str | Path = ".") -> None:
        super().__init__()
        self.project_root = Path(project_root).resolve()
        self.title("Jarvis Installer Center")
        self.geometry("920x640")
        self._build()
        self.refresh()

    def _build(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        header = ttk.Frame(root)
        header.pack(fill="x")
        ttk.Label(header, text="Jarvis Native Installer", font=("Segoe UI", 16, "bold")).pack(side="left")
        ttk.Button(header, text="Prüfen", command=self.refresh).pack(side="right")
        ttk.Button(header, text="Installer-Dateien schreiben", command=self.write_files).pack(side="right", padx=8)
        self.summary = ttk.Label(root, text="")
        self.summary.pack(fill="x", pady=(8, 8))
        cols = ("key", "status", "severity", "message", "path")
        self.tree = ttk.Treeview(root, columns=cols, show="headings", height=14)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=160 if col != "message" else 320)
        self.tree.pack(fill="both", expand=True)
        ttk.Label(root, text="Plan / Ausgabe").pack(anchor="w", pady=(10, 4))
        self.output = tk.Text(root, height=12, wrap="word")
        self.output.pack(fill="both", expand=False)

    def refresh(self) -> None:
        payload = installer_status(self.project_root)
        plan = installer_plan(self.project_root)
        self.summary.config(text=f"Status: {payload['status']} | Blocker: {len(payload['blockers'])} | Warnungen: {len(payload['warnings'])}")
        for item in self.tree.get_children():
            self.tree.delete(item)
        for check in payload["checks"]:
            self.tree.insert("", "end", values=(check["key"], "OK" if check["ok"] else "FEHLT", check["severity"], check["message"], check.get("path") or ""))
        self.output.delete("1.0", "end")
        self.output.insert("1.0", json.dumps(plan, indent=2, ensure_ascii=False))

    def write_files(self) -> None:
        payload = write_installer_artifacts(self.project_root)
        self.output.delete("1.0", "end")
        self.output.insert("1.0", json.dumps(payload, indent=2, ensure_ascii=False))
        if payload.get("ok"):
            messagebox.showinfo("Jarvis Installer", "Installer-Dateien wurden geschrieben.")
        else:
            messagebox.showwarning("Jarvis Installer", "Installer-Dateien wurden geschrieben, aber Blocker bleiben offen.")


def run(project_root: str | Path = ".") -> int:
    app = InstallerCenterGui(project_root)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
