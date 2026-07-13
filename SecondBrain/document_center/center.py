"""Document Center service + controller + Tkinter panel.

The service wires the import queue, preview builder, tags, history, and job
monitor to a runtime directory. The controller is headless (unit-testable). The
Tk panel adds drag & drop multi-import and a non-blocking preview pane.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from secondbrain.document_center.core import (
    DocumentHistory,
    ImportItem,
    ImportQueue,
    JobMonitor,
    PreviewBuilder,
    PreviewResult,
    TagStore,
)


class DocumentCenter:
    def __init__(self, runtime_dir: str | Path, *, on_indexed: Callable[[PreviewResult], None] | None = None) -> None:
        self.dir = Path(runtime_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.builder = PreviewBuilder()
        self.monitor = JobMonitor(self.dir / "import_jobs.jsonl")
        self.history = DocumentHistory(self.dir / "doc_history.jsonl")
        self.tags = TagStore(self.dir / "tags.json")
        self.queue = ImportQueue(self.builder, monitor=self.monitor, history=self.history, on_indexed=on_indexed)

    def import_paths(self, paths) -> list[ImportItem]:
        self.queue.enqueue(paths)
        return self.queue.process_all()

    def import_paths_async(self, paths, on_item=None, scheduler=None):
        self.queue.enqueue(paths)
        return self.queue.start_async(on_item=on_item, scheduler=scheduler)

    def preview(self, path: str | Path) -> PreviewResult:
        return self.builder.build(path)

    def set_tags(self, doc_id: str, tags: list[str]) -> list[str]:
        result = self.tags.set(doc_id, tags)
        self.history.record(doc_id, "tagged", tags=result)
        return result

    def get_tags(self, doc_id: str) -> list[str]:
        return self.tags.get(doc_id)

    def document_history(self, doc_id: str) -> list[dict[str, Any]]:
        return self.history.for_document(doc_id)

    def job_monitor_rows(self) -> list[dict[str, Any]]:
        return self.monitor.entries()


class DocumentCenterController:
    """Headless controller for the GUI panel."""

    def __init__(self, center: DocumentCenter) -> None:
        self.center = center

    def import_dropped(self, paths, on_item=None, scheduler=None):
        return self.center.import_paths_async(paths, on_item=on_item, scheduler=scheduler)

    def preview(self, path: str | Path) -> dict[str, Any]:
        return self.center.preview(path).to_dict()

    def job_rows(self) -> list[dict[str, Any]]:
        return self.center.job_monitor_rows()

    def set_tags(self, doc_id: str, tags: list[str]) -> list[str]:
        return self.center.set_tags(doc_id, tags)

    def history(self, doc_id: str) -> list[dict[str, Any]]:
        return self.center.document_history(doc_id)


def build_panel(master: Any, center: DocumentCenter) -> Any:
    """Build the Tk Document Center frame with drag & drop multi-import."""
    import tkinter as tk
    from tkinter import filedialog, ttk

    controller = DocumentCenterController(center)
    frame = ttk.Frame(master, padding=8)

    left = ttk.Frame(frame)
    left.grid(row=0, column=0, sticky="nsew")
    right = ttk.Frame(frame)
    right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=2)
    frame.rowconfigure(0, weight=1)

    cols = ("path", "state", "kind", "ocr")
    tree = ttk.Treeview(left, columns=cols, show="headings", height=14)
    for col, label, width in (("path", "Datei", 200), ("state", "Status", 90), ("kind", "Typ", 90), ("ocr", "OCR", 90)):
        tree.heading(col, text=label)
        tree.column(col, width=width, anchor="w")
    tree.grid(row=0, column=0, columnspan=3, sticky="nsew")
    left.rowconfigure(0, weight=1)
    left.columnconfigure(0, weight=1)

    preview_box = tk.Text(right, wrap="word", height=18, width=50)
    preview_box.grid(row=0, column=0, columnspan=3, sticky="nsew")
    right.rowconfigure(0, weight=1)
    right.columnconfigure(0, weight=1)
    status_var = tk.StringVar(value="Dateien hierher ziehen oder 'Importieren' klicken.")
    ttk.Label(frame, textvariable=status_var).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

    rows: dict[str, ImportItem] = {}

    def _row_values(item: ImportItem):
        pv = item.preview
        return (Path(item.path).name, item.state.value,
                pv.kind.value if pv else "-", pv.ocr_status.value if pv else "-")

    def on_item(item: ImportItem) -> None:
        rows[item.id] = item
        existing = {tree.item(i, "values")[0]: i for i in tree.get_children()}
        name = Path(item.path).name
        if name in existing:
            tree.item(existing[name], values=_row_values(item))
        else:
            tree.insert("", "end", iid=item.id, values=_row_values(item))
        errors = sum(1 for it in rows.values() if it.state.value == "error")
        status_var.set(f"Import: {len(rows)} Dateien | Fehler: {errors} (siehe Job Monitor)")

    def do_import(paths) -> None:
        if not paths:
            return
        status_var.set("Import laeuft (Vorschau blockiert die GUI nicht) ...")
        controller.import_dropped(list(paths), on_item=on_item, scheduler=frame.after)

    def pick_files() -> None:
        do_import(filedialog.askopenfilenames(parent=frame))

    def show_preview() -> None:
        sel = tree.focus()
        if not sel or sel not in rows:
            return
        data = controller.preview(rows[sel].path)
        preview_box.delete("1.0", "end")
        if data["is_error"]:
            preview_box.insert("end", f"[FEHLER] {data['parse_status']}\n{', '.join(data['parser_errors'])}\n")
        elif data["kind"] == "image":
            preview_box.insert("end", f"[BILD] {data['title']}\nOCR: {data['ocr_status']}\nMeta: {data['metadata']}\n")
        else:
            preview_box.insert("end", f"[{data['kind'].upper()}] {data['title']}  OCR: {data['ocr_status']}\n\n")
            preview_box.insert("end", data["preview_text"])

    tree.bind("<<TreeviewSelect>>", lambda _e: show_preview())

    ttk.Button(left, text="Importieren", command=pick_files).grid(row=1, column=0, sticky="ew", padx=2, pady=6)
    ttk.Button(left, text="Vorschau", command=show_preview).grid(row=1, column=1, sticky="ew", padx=2, pady=6)

    # Drag & drop: enabled when tkinterdnd2 is available, otherwise the file
    # dialog above is the fallback path.
    try:
        frame.drop_target_register("DND_Files")  # type: ignore[attr-defined]
        frame.dnd_bind("<<Drop>>", lambda e: do_import(frame.tk.splitlist(e.data)))  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001 - drag&drop optional; dialog remains
        pass

    return frame
