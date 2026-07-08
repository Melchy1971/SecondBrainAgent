"""GUI Connector Center.

Headless ``ConnectorCenterController`` (unit-testable) plus a lazy Tkinter panel.
Sync runs on a worker thread so the GUI never blocks; results are posted back via
the widget scheduler.
"""

from __future__ import annotations

import threading
from typing import Any, Callable

from secondbrain.connector_runtime.runtime import ConnectorRuntime


class ConnectorCenterController:
    def __init__(self, runtime: ConnectorRuntime) -> None:
        self.runtime = runtime

    def source_rows(self) -> list[dict[str, Any]]:
        return self.runtime.statuses()

    def dead_letters(self) -> list[dict[str, Any]]:
        return self.runtime.dead_letters.entries()

    def jobs(self) -> list[dict[str, Any]]:
        return self.runtime.jobs.entries()

    def sync(self, source_id: str) -> dict[str, Any]:
        return self.runtime.sync(source_id).to_dict()

    def sync_async(self, source_id: str, on_done: Callable[[dict], None],
                   on_error: Callable[[Exception], None] | None = None,
                   scheduler: Callable[[Callable[[], None]], None] | None = None) -> threading.Thread:
        def _schedule(fn: Callable[[], None]) -> None:
            (scheduler or (lambda f: f()))(fn)

        def _target() -> None:
            try:
                result = self.sync(source_id)
            except Exception as exc:  # noqa: BLE001 - surfaced to UI
                err = exc
                _schedule(lambda e=err: (on_error or (lambda _e: None))(e))
                return
            _schedule(lambda r=result: on_done(r))

        thread = threading.Thread(target=_target, daemon=True)
        thread.start()
        return thread


def build_panel(master: Any, runtime: ConnectorRuntime) -> Any:
    """Build the Tk Connector Center frame. Requires a display."""
    import tkinter as tk
    from tkinter import ttk

    controller = ConnectorCenterController(runtime)
    frame = ttk.Frame(master, padding=8)

    cols = ("source", "connector", "status", "last_sync", "error")
    tree = ttk.Treeview(frame, columns=cols, show="headings", height=10)
    for col, label, width in (
        ("source", "Quelle", 130), ("connector", "Connector", 130), ("status", "Status", 90),
        ("last_sync", "Letzter Sync", 170), ("error", "Fehler", 200),
    ):
        tree.heading(col, text=label)
        tree.column(col, width=width, anchor="w")
    tree.grid(row=0, column=0, columnspan=4, sticky="nsew")
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    status_var = tk.StringVar(value="")
    ttk.Label(frame, textvariable=status_var).grid(row=2, column=0, columnspan=4, sticky="w", pady=(6, 0))

    def refresh() -> None:
        for item in tree.get_children():
            tree.delete(item)
        for row in controller.source_rows():
            tag = row["status"]
            tree.insert("", "end", values=(row["source_id"], row["connector"], row["status"],
                                           row.get("last_sync_at") or "-", row.get("last_error") or ""), tags=(tag,))
        tree.tag_configure("error", foreground="#b00020")
        tree.tag_configure("stale", foreground="#a05a00")
        tree.tag_configure("fresh", foreground="#0a7a2f")

    def on_sync() -> None:
        sel = tree.focus()
        if not sel:
            return
        source_id = tree.item(sel, "values")[0]
        status_var.set(f"Sync '{source_id}' laeuft ...")

        def done(result: dict) -> None:
            job = result["job"]
            status_var.set(f"{source_id}: {job['state']} | Dok: {job['documents']} | DLQ: {job['dead_letters']}")
            refresh()

        controller.sync_async(source_id, done,
                              on_error=lambda e: status_var.set(f"Sync fehlgeschlagen: {e}"),
                              scheduler=frame.after)

    ttk.Button(frame, text="Sync", command=on_sync).grid(row=1, column=0, sticky="ew", padx=2, pady=6)
    ttk.Button(frame, text="Aktualisieren", command=refresh).grid(row=1, column=1, sticky="ew", padx=2, pady=6)

    refresh()
    return frame
