"""Tag Editor: Review Queue abarbeiten, Typ/Tags manuell korrigieren, Historie einsehen."""

from __future__ import annotations

import getpass
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from secondbrain.classification import ReviewQueue, TagHistory

FONT = "Segoe UI"


class TagEditorFrame(ttk.Frame):
    def __init__(self, master: tk.Misc, project_root: str | Path = ".") -> None:
        super().__init__(master, padding=8)
        self.project_root = Path(project_root)
        self.queue = ReviewQueue(self.project_root)
        self.history = TagHistory(self.project_root)

        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 6))
        ttk.Label(top, text="Tag Editor — Review Queue und manuelle Korrekturen",
                  font=(FONT, 12, "bold")).pack(side="left")
        ttk.Button(top, text="Neu laden", command=self.reload).pack(side="right")

        self.info_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.info_var, font=(FONT, 9)).pack(fill="x")

        columns = ("review", "dokument", "typ", "tags", "confidence", "erstellt")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=10)
        headings = ("Review", "Dokument", "Vorschlag Typ", "Vorschlag Tags", "Confidence", "Erstellt")
        widths = (110, 260, 100, 160, 80, 140)
        for column, heading, width in zip(columns, headings, widths):
            self.tree.heading(column, text=heading)
            self.tree.column(column, width=width, stretch=column in ("dokument", "tags"))
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        editor = ttk.LabelFrame(self, text="Korrektur (überschreibt den Vorschlag nachvollziehbar)",
                                padding=8)
        editor.pack(fill="x", pady=(8, 0))
        editor.columnconfigure(1, weight=1)
        ttk.Label(editor, text="Dokumenttyp:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.type_var = tk.StringVar(value="")
        ttk.Combobox(editor, textvariable=self.type_var,
                     values=("rechnung", "vertrag", "protokoll", "task", "projekt",
                             "prozess", "person", "quelle", "wissen", "inbox")
                     ).grid(row=0, column=1, sticky="ew")
        ttk.Label(editor, text="Tags (kommagetrennt):").grid(row=1, column=0, sticky="w",
                                                             padx=(0, 8), pady=(4, 0))
        self.tags_var = tk.StringVar(value="")
        ttk.Entry(editor, textvariable=self.tags_var).grid(row=1, column=1, sticky="ew", pady=(4, 0))
        ttk.Button(editor, text="Übernehmen", command=self.apply_correction).grid(
            row=0, column=2, rowspan=2, padx=(8, 0))

        ttk.Label(self, text="Tag-Historie des gewählten Dokuments:",
                  font=(FONT, 9, "bold")).pack(anchor="w", pady=(8, 0))
        self.history_text = tk.Text(self, height=6, wrap="word", borderwidth=0)
        self.history_text.pack(fill="x")

        self._items: dict[str, dict] = {}
        self.reload()

    def reload(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._items = {}
        open_items = self.queue.list_open(limit=200)
        self.info_var.set(f"Offene Reviews: {len(open_items)}")
        for item in open_items:
            self._items[item["review_id"]] = item
            suggestion = item.get("suggestion", {})
            self.tree.insert("", "end", iid=item["review_id"], values=(
                item["review_id"][:12],
                item["doc_ref"],
                suggestion.get("document_type", ""),
                ", ".join(suggestion.get("tags", [])),
                suggestion.get("confidence", ""),
                str(item.get("created_at", ""))[:19],
            ))
        self._show_history("")

    def _selected(self) -> dict | None:
        selection = self.tree.selection()
        return self._items.get(selection[0]) if selection else None

    def _on_select(self, _event: object | None = None) -> None:
        item = self._selected()
        if not item:
            return
        suggestion = item.get("suggestion", {})
        self.type_var.set(suggestion.get("document_type", ""))
        self.tags_var.set(", ".join(suggestion.get("tags", [])))
        self._show_history(item["doc_ref"])

    def _show_history(self, doc_ref: str) -> None:
        self.history_text.configure(state="normal")
        self.history_text.delete("1.0", "end")
        if doc_ref:
            entries = self.history.for_document(doc_ref, limit=10)
            lines = [
                f"{str(e['ts'])[:19]}  [{e['source']}]  {e.get('old_type') or '-'} -> {e.get('new_type') or '-'}"
                f"  Tags: {', '.join(e.get('new_tags', []))}"
                + (f"  ({e['editor']})" if e.get("editor") else "")
                for e in entries
            ]
            self.history_text.insert("1.0", "\n".join(lines) or "keine Einträge")
        self.history_text.configure(state="disabled")

    def apply_correction(self) -> None:
        item = self._selected()
        if not item:
            self.info_var.set("Kein Review ausgewählt.")
            return
        tags = [tag.strip() for tag in self.tags_var.get().split(",") if tag.strip()]
        try:
            editor = getpass.getuser()
        except Exception:
            editor = "gui"
        self.queue.resolve(
            item["review_id"],
            document_type=self.type_var.get().strip(),
            tags=tags,
            editor=editor,
        )
        self.reload()


class TagEditorWorkspaceFrame(TagEditorFrame):
    """Namenskonvention der übrigen Workspace-Panels."""
