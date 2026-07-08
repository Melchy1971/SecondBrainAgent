"""Secret Manager GUI (Tkinter) — v30.66.

WARNING: Windows/desktop GUI code. NOT executed/verified in the build sandbox
(no display). tkinter is imported lazily. The vault logic (secondbrain.secret_manager.*)
is fully unit-tested; only the widget layer is unverified here.

Secrets are never rendered in list views (metadata only) and never logged.
"""

from __future__ import annotations

from pathlib import Path

from secondbrain.secret_manager.vault import SecretVault
from secondbrain.secret_manager.health import vault_health


class SecretManagerGUI:
    def __init__(self, vault_path: str | Path, master=None) -> None:
        import tkinter as tk
        from tkinter import ttk, simpledialog, messagebox
        self.tk, self.ttk = tk, ttk
        self.simpledialog, self.messagebox = simpledialog, messagebox
        self.root = master or tk.Tk()
        self.vault = SecretVault(vault_path)
        self._build()

    def _build(self) -> None:  # pragma: no cover - GUI
        tk, ttk = self.tk, self.ttk
        self.root.title("SecondBrain — Secret Manager")
        bar = ttk.Frame(self.root); bar.pack(fill=tk.X)
        for label, cmd in [("Unlock", self.on_unlock), ("Add", self.on_add),
                           ("Rotate Master Key", self.on_rotate), ("Change Password", self.on_change_password),
                           ("Export", self.on_export), ("Import", self.on_import)]:
            ttk.Button(bar, text=label, command=cmd).pack(side=tk.LEFT, padx=2, pady=2)
        self.tree = ttk.Treeview(self.root, columns=("type", "version", "updated"), show="headings")
        for c, t in [("type", "Type"), ("version", "Version"), ("updated", "Updated")]:
            self.tree.heading(c, text=t)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.health_label = ttk.Label(self.root, anchor="w"); self.health_label.pack(fill=tk.X, side=tk.BOTTOM)
        self.refresh()

    def refresh(self) -> None:  # pragma: no cover - GUI
        for row in self.tree.get_children():
            self.tree.delete(row)
        for s in self.vault.list_secrets():      # metadata only, never values
            self.tree.insert("", "end", iid=s["name"], values=(s["type"], s["version"], s["updated_at"]))
        h = vault_health(self.vault)
        self.health_label.config(text=f"Status {h['status']} · {h['secret_count']} secrets · unlocked={h['unlocked']}")

    # ---- handlers (GUI-only) ---------------------------------------------
    def on_unlock(self):  # pragma: no cover - GUI
        pw = self.simpledialog.askstring("Unlock", "Master password:", show="*")
        if pw:
            try:
                self.vault.unlock(pw); self.refresh()
            except Exception:
                self.messagebox.showerror("Unlock", "Invalid master password")

    def on_add(self):  # pragma: no cover - GUI
        name = self.simpledialog.askstring("Add secret", "Name:")
        value = self.simpledialog.askstring("Add secret", "Value:", show="*")
        if name and value:
            self.vault.set_secret(name, value); self.refresh()

    def on_rotate(self):  # pragma: no cover - GUI
        pw = self.simpledialog.askstring("Rotate", "Master password:", show="*")
        if pw:
            self.vault.rotate_master_key(pw); self.refresh()

    def on_change_password(self):  # pragma: no cover - GUI
        old = self.simpledialog.askstring("Change password", "Old:", show="*")
        new = self.simpledialog.askstring("Change password", "New:", show="*")
        if old and new:
            self.vault.change_password(old, new); self.refresh()

    def on_export(self):  # pragma: no cover - GUI
        import json
        from tkinter import filedialog
        pw = self.simpledialog.askstring("Export", "Export password:", show="*")
        target = filedialog.asksaveasfilename(defaultextension=".sbvault")
        if pw and target:
            Path(target).write_text(json.dumps(self.vault.export_bundle(pw)), encoding="utf-8")

    def on_import(self):  # pragma: no cover - GUI
        import json
        from tkinter import filedialog
        pw = self.simpledialog.askstring("Import", "Export password:", show="*")
        src = filedialog.askopenfilename()
        if pw and src:
            self.vault.import_bundle(json.loads(Path(src).read_text(encoding="utf-8")), pw)
            self.refresh()

    def run(self):  # pragma: no cover - GUI
        self.root.mainloop()
