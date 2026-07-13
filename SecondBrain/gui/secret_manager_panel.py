"""Native GUI Secret Manager panel (Tkinter).

Binds to ``secondbrain.vault.SecretManager``. The table shows masked values only;
a secret is revealed on explicit demand (and that reveal is audited). Long-running
actions (plaintext-leak scan, import/export) run on a worker thread and post their
result back to the UI thread via ``after`` so the GUI never blocks.

Tkinter is imported lazily so importing this module has no display dependency.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Callable

from secondbrain.vault.manager import SecretManager


class SecretManagerController:
    """Headless controller between the Tk widgets and the SecretManager.

    Kept UI-framework-free so it can be unit-tested without a display.
    """

    def __init__(self, manager: SecretManager) -> None:
        self.manager = manager

    def table_rows(self, *, workspace: str | None = None) -> list[dict[str, Any]]:
        return self.manager.rows(workspace=workspace)

    def add(self, name: str, value: str, *, workspace: str = "default") -> str:
        return self.manager.add_secret(name, value, workspace=workspace)

    def reveal(self, name: str, *, workspace: str = "default") -> str:
        return self.manager.reveal_secret(name, workspace=workspace)

    def delete(self, name: str, *, workspace: str = "default") -> bool:
        return self.manager.delete_secret(name, workspace=workspace)

    def rotate(self) -> int:
        return self.manager.rotate_key()

    def health(self, scan_paths: list[str | Path] | None = None) -> dict[str, Any]:
        return self.manager.health(scan_paths=scan_paths)

    def run_async(self, work: Callable[[], Any], on_done: Callable[[Any], None],
                  on_error: Callable[[Exception], None] | None = None,
                  scheduler: Callable[[Callable[[], None]], None] | None = None) -> threading.Thread:
        """Run ``work`` on a worker thread; deliver the result via ``scheduler``.

        ``scheduler`` is normally ``widget.after`` so the callback runs on the UI
        thread. Defaulting to direct call keeps the controller testable.
        """
        def _schedule(fn: Callable[[], None]) -> None:
            (scheduler or (lambda f: f()))(fn)

        def _target() -> None:
            try:
                result = work()
            except Exception as exc:  # noqa: BLE001 - surfaced to the UI, not swallowed
                err = exc
                _schedule(lambda e=err: (on_error or (lambda _e: None))(e))
                return
            _schedule(lambda r=result: on_done(r))

        thread = threading.Thread(target=_target, daemon=True)
        thread.start()
        return thread


def build_panel(master: Any, manager: SecretManager) -> Any:
    """Build and return the Tk frame for the Secret Manager. Requires a display."""
    import tkinter as tk
    from tkinter import messagebox, simpledialog, ttk

    controller = SecretManagerController(manager)
    frame = ttk.Frame(master, padding=8)

    columns = ("workspace", "name", "value", "dek_version", "origin", "updated_at")
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=12)
    for col, label, width in (
        ("workspace", "Workspace", 100), ("name", "Name", 180), ("value", "Wert", 110),
        ("dek_version", "Key v", 50), ("origin", "Herkunft", 110), ("updated_at", "Aktualisiert", 170),
    ):
        tree.heading(col, text=label)
        tree.column(col, width=width, anchor="w")
    tree.grid(row=0, column=0, columnspan=6, sticky="nsew")
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    status = tk.StringVar(value="")
    ttk.Label(frame, textvariable=status).grid(row=2, column=0, columnspan=6, sticky="w", pady=(6, 0))

    def refresh() -> None:
        for item in tree.get_children():
            tree.delete(item)
        for row in controller.table_rows():
            tree.insert("", "end", values=(row["workspace"], row["name"], row["value_masked"],
                                           row["dek_version"], row["origin"], row["updated_at"]))

    def _selected() -> tuple[str, str] | None:
        sel = tree.focus()
        if not sel:
            return None
        vals = tree.item(sel, "values")
        return (vals[0], vals[1])

    def on_add() -> None:
        name = simpledialog.askstring("Secret hinzufuegen", "Name:", parent=frame)
        if not name:
            return
        value = simpledialog.askstring("Secret hinzufuegen", "Wert:", parent=frame, show="*")
        if not value:
            return
        controller.add(name, value)
        status.set(f"Secret '{name}' gespeichert (verschluesselt).")
        refresh()

    def on_reveal() -> None:
        target = _selected()
        if not target:
            return
        workspace, name = target
        value = controller.reveal(name, workspace=workspace)
        messagebox.showinfo("Secret", f"{name} = {value}", parent=frame)
        status.set(f"'{name}' angezeigt (Audit-Eintrag geschrieben).")

    def on_delete() -> None:
        target = _selected()
        if not target:
            return
        workspace, name = target
        if messagebox.askyesno("Loeschen", f"Secret '{name}' loeschen?", parent=frame):
            controller.delete(name, workspace=workspace)
            status.set(f"'{name}' geloescht.")
            refresh()

    def on_rotate() -> None:
        status.set("Key-Rotation laeuft ...")

        def done(version: int) -> None:
            status.set(f"Key rotiert. Aktive DEK-Version: {version}. Alle Secrets neu verschluesselt.")
            refresh()

        controller.run_async(controller.rotate, done,
                             on_error=lambda e: status.set(f"Rotation fehlgeschlagen: {e}"),
                             scheduler=frame.after)

    def on_health() -> None:
        status.set("Health-Check laeuft ...")

        def done(report: dict) -> None:
            leaks = len(report.get("leaks", []))
            status.set(f"Vault {report['status']} | Secrets: {report['secret_count']} | Leaks: {leaks}")

        controller.run_async(lambda: controller.health(scan_paths=[Path(".") / "logs"]), done,
                             on_error=lambda e: status.set(f"Health-Check fehlgeschlagen: {e}"),
                             scheduler=frame.after)

    buttons = (
        ("Hinzufuegen", on_add), ("Anzeigen", on_reveal), ("Loeschen", on_delete),
        ("Key rotieren", on_rotate), ("Health", on_health), ("Aktualisieren", refresh),
    )
    for idx, (label, cmd) in enumerate(buttons):
        ttk.Button(frame, text=label, command=cmd).grid(row=1, column=idx, sticky="ew", padx=2, pady=6)

    refresh()
    return frame
