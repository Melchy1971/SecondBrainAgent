from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from secondbrain.native.memory_explorer import MemoryExplorer


def run_memory_explorer_gui(project_root: str | Path = ".") -> int:
    explorer = MemoryExplorer(project_root)
    root = tk.Tk()
    root.title("Jarvis · Memory Explorer")
    root.geometry("980x680")

    query_var = tk.StringVar()
    kind_var = tk.StringVar()
    detail = tk.Text(root, height=14, wrap="word")
    tree = ttk.Treeview(root, columns=("kind", "source", "tags", "favorite"), show="headings")
    for col, title, width in [("kind", "Art", 120), ("source", "Quelle", 180), ("tags", "Tags", 260), ("favorite", "Favorit", 80)]:
        tree.heading(col, text=title)
        tree.column(col, width=width)

    entries: list[dict] = []

    def refresh() -> None:
        nonlocal entries
        payload = explorer.entries(query=query_var.get(), kind=kind_var.get(), include_archived=True, limit=500)
        entries = payload.get("memories", [])
        tree.delete(*tree.get_children())
        for idx, row in enumerate(entries):
            tree.insert("", "end", iid=str(idx), values=(row.get("kind"), row.get("source"), ", ".join(row.get("tags") or []), "ja" if row.get("favorite") else ""))
        detail.delete("1.0", "end")
        detail.insert("end", json.dumps(explorer.status(), indent=2, ensure_ascii=False))

    def selected() -> dict | None:
        sel = tree.selection()
        if not sel:
            return None
        return entries[int(sel[0])]

    def show_detail(_event=None) -> None:
        row = selected()
        detail.delete("1.0", "end")
        if row:
            detail.insert("end", json.dumps(row, indent=2, ensure_ascii=False))

    def add_memory() -> None:
        text = detail.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Jarvis", "Kein Text im Detailfeld.")
            return
        payload = explorer.add(text, kind=kind_var.get() or "working", source="native_gui")
        if not payload.get("ok"):
            messagebox.showerror("Jarvis", str(payload))
        refresh()

    def mark_favorite() -> None:
        row = selected()
        if row:
            explorer.favorite(row["memory_id"], not bool(row.get("favorite")))
            refresh()

    def archive() -> None:
        row = selected()
        if row:
            explorer.archive(row["memory_id"])
            refresh()

    def export_json() -> None:
        payload = explorer.export("json")
        messagebox.showinfo("Jarvis", f"Export erstellt:\n{payload.get('path')}")

    bar = ttk.Frame(root, padding=8)
    bar.pack(fill="x")
    ttk.Label(bar, text="Suche").pack(side="left")
    ttk.Entry(bar, textvariable=query_var, width=32).pack(side="left", padx=6)
    ttk.Label(bar, text="Art").pack(side="left")
    ttk.Entry(bar, textvariable=kind_var, width=16).pack(side="left", padx=6)
    ttk.Button(bar, text="Aktualisieren", command=refresh).pack(side="left", padx=4)
    ttk.Button(bar, text="Favorit", command=mark_favorite).pack(side="left", padx=4)
    ttk.Button(bar, text="Archivieren", command=archive).pack(side="left", padx=4)
    ttk.Button(bar, text="Export JSON", command=export_json).pack(side="left", padx=4)

    tree.pack(fill="both", expand=True, padx=8, pady=8)
    tree.bind("<<TreeviewSelect>>", show_detail)
    detail.pack(fill="both", expand=False, padx=8, pady=(0, 8))
    ttk.Button(root, text="Detailtext als neue Memory speichern", command=add_memory).pack(anchor="e", padx=8, pady=(0, 8))

    refresh()
    root.mainloop()
    return 0
