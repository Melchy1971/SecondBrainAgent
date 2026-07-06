"""Native AI Workspace Import Center backed by the existing import runtime."""
from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from secondbrain.importing import ImportCenterService, ImportProgress, StreamingImportService


class StreamingImportFrame(ttk.Frame):
    def __init__(self, master: tk.Misc, project_root: str | Path):
        super().__init__(master)
        self.project_root = Path(project_root)
        self.source = tk.StringVar(value="file")
        self.batch_size = tk.IntVar(value=500)
        self.progress = tk.DoubleVar(value=0)
        self.message = tk.StringVar(value="Bereit")
        self.resources = tk.StringVar(value="Worker 0/0 · CPU -- · RAM --")
        self._runtime_service = StreamingImportService(self.project_root, batch_size=self.batch_size.get())
        self.center = ImportCenterService(self.project_root, engine=self._runtime_service)
        self.bind("<Destroy>", self._shutdown, add="+")
        self._build()
        self.reload()

    def _build(self) -> None:
        bar = ttk.Frame(self, padding=6); bar.pack(fill="x")
        ttk.Label(bar, text="Quelle").pack(side="left")
        sources = ("file", "chatgpt", "claude", "gemini", "perplexity", "librechat", "anythingllm",
                   "openwebui", "openai_export", "obsidian", "notion", "paperless", "onenote")
        ttk.Combobox(bar, textvariable=self.source, values=sources, state="readonly", width=14).pack(side="left", padx=4)
        ttk.Label(bar, text="Batch").pack(side="left", padx=(12, 2))
        ttk.Spinbox(bar, from_=1, to=10000, textvariable=self.batch_size, width=7).pack(side="left")
        ttk.Button(bar, text="Datei importieren", command=self.start).pack(side="left", padx=8)
        ttk.Button(bar, text="Aktualisieren", command=self.reload).pack(side="left", padx=4)

        controls = ttk.Frame(self, padding=(6, 0)); controls.pack(fill="x")
        ttk.Button(controls, text="Pause", command=self.pause).pack(side="left")
        ttk.Button(controls, text="Continue", command=self.resume).pack(side="left", padx=3)
        ttk.Button(controls, text="Retry", command=self.retry).pack(side="left")
        ttk.Button(controls, text="Stop", command=self.stop).pack(side="left", padx=3)
        ttk.Label(controls, textvariable=self.resources).pack(side="right")
        ttk.Progressbar(self, variable=self.progress, maximum=100).pack(fill="x", padx=6)

        columns = ("file", "eta", "progress", "chats", "documents", "chunks", "embeddings", "workers", "status")
        self.sessions = ttk.Treeview(self, columns=columns, show="headings", height=12)
        labels = {"file": "Datei", "eta": "ETA", "progress": "Fortschritt", "chats": "Importierte Chats",
                  "documents": "Dokumente", "chunks": "Chunks", "embeddings": "Embeddings",
                  "workers": "Worker", "status": "Status"}
        for column in columns:
            self.sessions.heading(column, text=labels[column]); self.sessions.column(column, width=105, anchor="w")
        self.sessions.column("file", width=220)
        self.sessions.pack(fill="both", expand=True, padx=6, pady=6)

        details = ttk.Panedwindow(self, orient="horizontal"); details.pack(fill="both", expand=True, padx=6)
        log_frame, error_frame = ttk.LabelFrame(details, text="Logs"), ttk.LabelFrame(details, text="Fehler")
        self.logs, self.errors = tk.Text(log_frame, height=6, wrap="none", state="disabled"), tk.Text(error_frame, height=6, wrap="word", state="disabled")
        self.logs.pack(fill="both", expand=True); self.errors.pack(fill="both", expand=True)
        details.add(log_frame, weight=2); details.add(error_frame, weight=1)

        quality_tabs = ttk.Notebook(self); quality_tabs.pack(fill="both", expand=True, padx=6, pady=6)
        dashboard = ttk.Frame(quality_tabs); warnings = ttk.Frame(quality_tabs); duplicates = ttk.Frame(quality_tabs)
        quality_tabs.add(dashboard, text="Quality Dashboard")
        quality_tabs.add(warnings, text="Import Warnings")
        quality_tabs.add(duplicates, text="Duplicate Viewer")
        self.quality_summary = tk.StringVar(value="Noch keine Qualitätsdaten")
        ttk.Label(dashboard, textvariable=self.quality_summary, padding=10).pack(anchor="w")
        self.warning_rows = ttk.Treeview(warnings, columns=("file", "score", "warning"), show="headings", height=5)
        for column, label in (("file", "Dokument"), ("score", "Score"), ("warning", "Warnung")):
            self.warning_rows.heading(column, text=label)
        self.warning_rows.pack(fill="both", expand=True)
        self.duplicate_rows = ttk.Treeview(duplicates, columns=("type", "document", "match", "similarity"), show="headings", height=5)
        for column, label in (("type", "Typ"), ("document", "Dokument"), ("match", "Duplikat"), ("similarity", "Ähnlichkeit")):
            self.duplicate_rows.heading(column, text=label)
        self.duplicate_rows.pack(fill="both", expand=True)
        ttk.Label(self, textvariable=self.message).pack(fill="x", padx=6)

    def _service(self) -> StreamingImportService:
        self._runtime_service.batch_size = max(1, self.batch_size.get())
        return self._runtime_service

    def reload(self) -> None:
        payload = self.center.status()
        for item in self.sessions.get_children(): self.sessions.delete(item)
        for row in payload["sessions"]:
            self.sessions.insert("", "end", iid=row["session_id"], values=(row["file"], row["eta"], f"{row['progress']:.1f}%",
                row["imported_chats"], row["documents"], row["chunks"], row["embeddings"], row["workers"], row["status"]))
        if payload["sessions"]:
            self.progress.set(payload["sessions"][0]["progress"])
        cpu, ram, workers = payload["cpu"], payload["ram"], payload["workers"]
        cpu_text = "--" if cpu["percent"] is None else f"{cpu['percent']:.1f}%"
        ram_text = "--" if ram["rss_bytes"] is None else f"{ram['rss_bytes'] / 1024**2:.0f} MB"
        self.resources.set(f"Worker {workers['active']}/{workers['configured']} · CPU {cpu_text} · RAM {ram_text}")
        history = self.center.history(limit=80)
        lines = [f"{item.get('updated_at') or item.get('created_at') or ''} {item.get('kind','')} {item.get('status') or item.get('event','')} {item.get('title','')}" for item in history["events"]]
        errors = [f"{item['file']}: {item['error']}" for item in payload["errors"]]
        self._set_text(self.logs, "\n".join(lines[-80:]))
        self._set_text(self.errors, "\n".join(errors) or "Keine Fehler")
        quality = self.center.quality_dashboard()
        self.quality_summary.set(f"Dokumente {quality['documents']} · Ø Score {quality['average_score']:.1f} · Niedrig {quality['low_quality']} · Warnungen {quality['warnings']}")
        for item in self.warning_rows.get_children(): self.warning_rows.delete(item)
        for row in self.center.import_warnings():
            self.warning_rows.insert("", "end", values=(row["title"], row["score"], row["warning"]))
        for item in self.duplicate_rows.get_children(): self.duplicate_rows.delete(item)
        for row in self.center.duplicates():
            self.duplicate_rows.insert("", "end", values=(row.get("type"), row.get("document_id"), row.get("duplicate_document_id", ""), f"{100 * float(row.get('similarity', 0)):.1f}%"))

    def start(self) -> None:
        patterns = "*.pst *.eml *.pdf *.docx *.xlsx *.csv *.txt *.md *.markdown *.json *.jsonl *.ndjson *.zip"
        path = filedialog.askopenfilename(parent=self, filetypes=[("Enterprise Import", patterns)])
        if path:
            doc_sources = {"obsidian", "notion", "paperless", "onenote"}
            doc_suffixes = {".pst", ".eml", ".pdf", ".docx", ".xlsx", ".csv", ".txt", ".md", ".markdown"}
            is_document = Path(path).suffix.lower() in doc_suffixes or self.source.get() in doc_sources
            self._run(lambda service: service.import_document(path, source=self.source.get(), progress=self._progress) if is_document else service.import_file(path, source=self.source.get(), progress=self._progress))

    def resume(self) -> None:
        session_id = self._selected_session()
        if session_id: self._run(lambda service: service.continue_import(session_id, progress=self._progress))

    def pause(self) -> None: self._control("pause")

    def retry(self) -> None:
        session_id = self._selected_session()
        if session_id: self._run(lambda service: service.retry(session_id, progress=self._progress))

    def stop(self) -> None: self._control("stop")

    def _selected_session(self) -> str | None:
        selected = self.sessions.selection()
        return str(selected[0]) if selected else None

    def _control(self, action: str) -> None:
        session_id = self._selected_session()
        if session_id:
            getattr(self.center, action)(session_id); self.reload()

    def _run(self, operation) -> None:
        self.message.set("Import läuft …")
        def worker():
            try:
                service = self._service(); service.scheduler.start(); session = operation(service)
                self.after(0, lambda: self.message.set(f"{session.status}: {session.imported_chats} Datensätze, {session.chunks} Chunks"))
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                self.after(0, lambda error=error: messagebox.showerror("Import Center", error, parent=self))
            finally:
                self.after(0, self.reload)
        threading.Thread(target=worker, daemon=True, name="streaming-import").start()

    @staticmethod
    def _set_text(widget: tk.Text, value: str) -> None:
        widget.configure(state="normal"); widget.delete("1.0", "end"); widget.insert("1.0", value); widget.configure(state="disabled")

    def _shutdown(self, event) -> None:
        if event.widget is self: self._runtime_service.scheduler.stop()

    def _progress(self, progress: ImportProgress) -> None:
        self.after(0, lambda: self.progress.set(progress.percent))
