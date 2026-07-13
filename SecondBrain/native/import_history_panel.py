"""Import-Historie in der Desktop-Shell: Status je Datei, Retry, Stufenverlauf."""

from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from secondbrain.import_pipeline import ImportHistory, UnifiedImportPipeline

FONT = "Segoe UI"


class ImportHistoryFrame(ttk.Frame):
    def __init__(self, master: tk.Misc, project_root: str | Path = ".") -> None:
        super().__init__(master, padding=8)
        self.project_root = Path(project_root)
        self.history = ImportHistory(self.project_root)

        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 6))
        ttk.Label(top, text="Import-Historie — einheitliche Pipeline (lokal + Connector)",
                  font=(FONT, 12, "bold")).pack(side="left")
        ttk.Button(top, text="Neu laden", command=self.reload).pack(side="right", padx=(4, 0))
        ttk.Button(top, text="Offene verarbeiten", command=self.process_open).pack(side="right", padx=(4, 0))
        ttk.Button(top, text="Ausgewählten Job erneut einreihen",
                   command=self.retry_selected).pack(side="right")

        self.counts_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.counts_var, font=(FONT, 9)).pack(fill="x")

        filters = ttk.Frame(self)
        filters.pack(fill="x", pady=4)
        ttk.Label(filters, text="Status:").pack(side="left")
        self.status_var = tk.StringVar(value="")
        ttk.Combobox(filters, textvariable=self.status_var, width=14, state="readonly",
                     values=("", "queued", "parsing", "classified", "chunked", "embedded",
                             "indexed", "failed", "dead_letter", "duplicate", "ocr_required")
                     ).pack(side="left", padx=(2, 10))
        ttk.Button(filters, text="Filtern", command=self.reload).pack(side="left")

        columns = ("job", "quelle", "art", "status", "versuche", "typ", "chunks", "fehler")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=12)
        headings = ("Job", "Quelle", "Art", "Status", "Versuche", "Dok-Typ", "Chunks", "Fehler")
        widths = (120, 240, 80, 90, 60, 90, 55, 220)
        for column, heading, width in zip(columns, headings, widths):
            self.tree.heading(column, text=heading)
            self.tree.column(column, width=width, stretch=column in ("quelle", "fehler"))
        self.tree.bind("<<TreeviewSelect>>", self._show_detail)
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        ttk.Label(self, text="Stufenverlauf / Lineage:", font=(FONT, 9, "bold")).pack(anchor="w", pady=(6, 0))
        self.detail_text = tk.Text(self, height=7, wrap="word", borderwidth=0)
        self.detail_text.pack(fill="x")

        self._jobs_by_id: dict[str, dict] = {}
        self.reload()

    def reload(self) -> None:
        snapshot = self.history.snapshot(status=self.status_var.get() or None, limit=300)
        counts = ", ".join(f"{k}={v}" for k, v in sorted(snapshot["counts"].items()))
        self.counts_var.set(f"Bestand: {counts or 'leer'}")
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._jobs_by_id = {}
        for job in reversed(snapshot["jobs"]):
            self._jobs_by_id[job["job_id"]] = job
            self.tree.insert("", "end", iid=job["job_id"], values=(
                job["job_id"][:14],
                job["source_ref"],
                job["connector"] or job["source_kind"],
                job["status"] + (" (OCR)" if job["ocr_required"] else ""),
                job["attempts"],
                job["document_type"],
                job["chunk_count"],
                f"[{job['error_category']}] {job['error']}" if job["error"] else "",
            ))

    def _selected_job_id(self) -> str:
        selection = self.tree.selection()
        return selection[0] if selection else ""

    def _show_detail(self, _event: object | None = None) -> None:
        job = self._jobs_by_id.get(self._selected_job_id())
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", "end")
        if job:
            self.detail_text.insert("1.0", json.dumps(
                {"stage_history": job["stage_history"],
                 "tags": job["tags"], "duplicate_of": job["duplicate_of"]},
                indent=1, ensure_ascii=False))
        self.detail_text.configure(state="disabled")

    def retry_selected(self) -> None:
        job_id = self._selected_job_id()
        if job_id:
            UnifiedImportPipeline(self.project_root).retry(job_id)
            self.reload()

    def process_open(self) -> None:
        UnifiedImportPipeline(self.project_root).process_batch()
        self.reload()


class ImportHistoryWorkspaceFrame(ImportHistoryFrame):
    """Namenskonvention der übrigen Workspace-Panels."""
