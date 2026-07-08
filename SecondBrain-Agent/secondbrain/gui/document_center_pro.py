"""Document Center Pro (Tkinter GUI) — v30.65.

WARNING: This is Windows/desktop GUI code. It is NOT executed or verified in the
build sandbox (no display). tkinter is imported lazily so importing this module
never fails headless. The document LOGIC it wires to (secondbrain.documents.*) is
fully unit-tested; the widget rendering is verified only on the target machine.

Additive: does not modify the existing document center.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from secondbrain.documents.preview import resolve, markdown_to_html, highlight
from secondbrain.documents.upload_queue import UploadQueue
from secondbrain.documents.import_history import ImportHistoryStore
from secondbrain.documents.tags import TagStore
from secondbrain.documents.versioning import VersionStore
from secondbrain.documents.compare import diff_documents
from secondbrain.documents.ocr_status import OcrStatusTracker


class DocumentCenterPro:
    """Composes the document-logic services with a Tkinter UI.

    All heavy lifting is delegated to the tested services; the class only lays out
    widgets and forwards events, so the untested surface is minimal.
    """

    def __init__(self, master=None, *, tag_store: TagStore | None = None) -> None:
        import tkinter as tk                      # lazy: no display needed to import module
        from tkinter import ttk
        self.tk = tk
        self.ttk = ttk
        self.root = master or tk.Tk()
        self.queue = UploadQueue()
        self.history = ImportHistoryStore()
        self.tags = tag_store or TagStore()
        self.versions = VersionStore()
        self.ocr = OcrStatusTracker()
        self._build()

    def _build(self) -> None:  # pragma: no cover - GUI, not run headless
        tk, ttk = self.tk, self.ttk
        self.root.title("SecondBrain — Document Center Pro")
        self.paned = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)
        self.sidebar = ttk.Frame(self.paned, width=260)
        self.preview = ttk.Frame(self.paned)
        self.paned.add(self.sidebar, weight=0)
        self.paned.add(self.preview, weight=1)
        self.status = ttk.Label(self.root, text="Ready", anchor="w")
        self.status.pack(fill=tk.X, side=tk.BOTTOM)
        self._build_queue_panel()
        self._enable_drag_and_drop()

    def _build_queue_panel(self) -> None:  # pragma: no cover - GUI
        ttk = self.ttk
        self.queue_view = ttk.Treeview(self.sidebar, columns=("status", "progress"), show="tree headings")
        self.queue_view.heading("status", text="Status")
        self.queue_view.heading("progress", text="%")
        self.queue_view.pack(fill="both", expand=True)

    def _enable_drag_and_drop(self) -> None:  # pragma: no cover - GUI
        # tkinterdnd2 provides real OS drag/drop; degrade gracefully if unavailable.
        try:
            self.root.tk.call("package", "require", "tkdnd")
            self.root.drop_target_register("DND_Files")
            self.root.dnd_bind("<<Drop>>", self._on_drop)
        except Exception:
            self.status.config(text="Drag&drop unavailable (install tkdnd/tkinterdnd2)")

    def _on_drop(self, event) -> None:  # pragma: no cover - GUI
        paths = self.root.tk.splitlist(event.data)
        self.add_files(paths)

    # ---- logic-facing methods (testable without a display) ----------------
    def add_files(self, paths) -> list[dict]:
        added = []
        for p in paths:
            size = Path(p).stat().st_size if Path(p).exists() else 0
            item = self.queue.enqueue(str(p), size)
            added.append({"id": item.id, "path": item.path, "preview": resolve(item.path).kind})
        return added

    def preview_for(self, path: str) -> dict[str, Any]:
        kind = resolve(path)
        payload: dict[str, Any] = {"kind": kind.kind, "renderer": kind.renderer, "mime": kind.mime}
        if kind.kind == "markdown" and Path(path).exists():
            payload["html"] = markdown_to_html(Path(path).read_text(encoding="utf-8", errors="replace"))
        elif kind.kind == "code" and Path(path).exists():
            payload["tokens"] = [(t.text, t.type) for t in
                                 highlight(Path(path).read_text(encoding="utf-8", errors="replace"), kind.language)]
        return payload

    def compare_versions(self, doc_id: str, v1: int, v2: int) -> dict:
        return diff_documents(self.versions.content(doc_id, v1), self.versions.content(doc_id, v2))

    def run(self) -> None:  # pragma: no cover - GUI event loop
        self.root.mainloop()


def launch(**kw) -> "DocumentCenterPro":  # pragma: no cover - GUI
    app = DocumentCenterPro(**kw)
    app.run()
    return app
