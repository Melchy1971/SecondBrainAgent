"""Real Import Center panel backed by StreamingImportService."""
from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from secondbrain.importing import ImportProgress, StreamingImportService


class StreamingImportFrame(ttk.Frame):
    def __init__(self, master: tk.Misc, project_root: str | Path):
        super().__init__(master)
        self.project_root = Path(project_root)
        self.source = tk.StringVar(value="file")
        self.batch_size = tk.IntVar(value=500)
        self.progress = tk.DoubleVar(value=0)
        self.message = tk.StringVar(value="Bereit")
        self._build(); self.reload()

    def _build(self) -> None:
        bar = ttk.Frame(self, padding=6); bar.pack(fill="x")
        ttk.Label(bar, text="Quelle").pack(side="left")
        ttk.Combobox(bar, textvariable=self.source, values=("file", "chatgpt", "claude", "gemini", "json", "jsonl", "markdown"), state="readonly", width=12).pack(side="left", padx=4)
        ttk.Label(bar, text="Batch").pack(side="left", padx=(12, 2))
        ttk.Spinbox(bar, from_=1, to=10000, textvariable=self.batch_size, width=7).pack(side="left")
        ttk.Button(bar, text="Datei importieren", command=self.start).pack(side="left", padx=8)
        ttk.Button(bar, text="Fortsetzen", command=self.resume).pack(side="left")
        ttk.Button(bar, text="Aktualisieren", command=self.reload).pack(side="left", padx=4)
        ttk.Progressbar(self, variable=self.progress, maximum=100).pack(fill="x", padx=6)
        self.sessions = ttk.Treeview(self, columns=("source", "bytes", "position", "chats", "chunks", "status"), show="tree headings")
        self.sessions.heading("#0", text="Session / Datei")
        for column in ("source", "bytes", "position", "chats", "chunks", "status"): self.sessions.heading(column, text=column.title())
        self.sessions.pack(fill="both", expand=True, padx=6, pady=6)
        ttk.Label(self, textvariable=self.message).pack(fill="x", padx=6)

    def _service(self) -> StreamingImportService:
        return StreamingImportService(self.project_root, batch_size=self.batch_size.get())

    def reload(self) -> None:
        payload = self._service().status()
        for item in self.sessions.get_children(): self.sessions.delete(item)
        for row in payload["sessions"]:
            label = f"{row['session_id']} · {Path(row['file_path']).name}"
            self.sessions.insert("", "end", iid=row["session_id"], text=label,
                values=(row["source"], f"{row['bytes_processed']}/{row['file_size']}", row["position"], row["imported_chats"], row["chunks"], row["status"]))

    def start(self) -> None:
        path = filedialog.askopenfilename(parent=self, filetypes=[("Streaming Import", "*.json *.jsonl *.ndjson *.md *.markdown *.zip")])
        if path: self._run(lambda service: service.import_file(path, source=self.source.get(), progress=self._progress))

    def resume(self) -> None:
        selected = self.sessions.selection()
        if selected: self._run(lambda service: service.resume(selected[0], progress=self._progress))

    def _run(self, operation) -> None:
        self.message.set("Import läuft …")
        def worker():
            try:
                session = operation(self._service())
                self.after(0, lambda: self.message.set(f"{session.status}: {session.imported_chats} Datensätze, {session.chunks} Chunks"))
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                self.after(0, lambda error=error: messagebox.showerror("Streaming Import", error, parent=self))
            finally:
                self.after(0, self.reload)
        threading.Thread(target=worker, daemon=True, name="streaming-import").start()

    def _progress(self, progress: ImportProgress) -> None:
        self.after(0, lambda: self.progress.set(progress.percent))
