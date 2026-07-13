"""Einstellungen-Editor für die Desktop-Shell (AIWorkspaceApp) und native App.

Ein wiederverwendbarer, in Bereiche gegliederter Editor über der zentralen
RuntimeConfig: KI/Embedding, Datenbank, GUI, Sprache, Pfade, Secrets.
Nicht-Secrets werden nach config.json geschrieben, Secrets in die .env;
maskierte Secrets bleiben unangetastet. GUI und CLI nutzen dieselbe Quelle.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Any, Callable

from secondbrain.native.settings_panel import NativeSettingsPanel

FONT = "Segoe UI"

ORIGIN_LABELS = {
    "environ": "Umgebungsvariable",
    "dotenv": ".env",
    "workspace_config": "config.json (Workspace)",
    "appdata_config": "config.json (AppData)",
    "gui_settings_legacy": "GUI-Settings (Alt)",
    "default": "Default",
}


def collect_values(field_vars: dict[str, tuple[str, Any]]) -> dict[str, str]:
    """Formularwerte -> Stringwerte für RuntimeConfig.set_values (rein, testbar)."""
    values: dict[str, str] = {}
    for key, (field_type, var) in field_vars.items():
        raw = var.get()
        if field_type == "bool":
            values[key] = "true" if raw else "false"
        else:
            values[key] = str(raw)
    return values


class SettingsEditorFrame(ttk.Frame):
    """Editierbare Einstellungen, gegliedert nach Bereichen, mit BLOCKED-Banner."""

    def __init__(
        self,
        master: tk.Misc,
        project_root: str | Path = ".",
        on_theme_change: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(master, padding=8)
        self.panel = NativeSettingsPanel(project_root)
        self.on_theme_change = on_theme_change
        self._field_vars: dict[str, tuple[str, Any]] = {}

        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 6))
        ttk.Label(top, text="Zentrale Konfiguration — identisch für GUI und CLI",
                  font=(FONT, 12, "bold")).pack(side="left")
        ttk.Button(top, text="Neu laden", command=self.reload).pack(side="right", padx=(4, 0))
        ttk.Button(top, text="Speichern", command=self.save).pack(side="right")

        self.result_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.result_var).pack(fill="x")

        holder = ttk.Frame(self)
        holder.pack(fill="both", expand=True, pady=(6, 0))
        self._canvas = tk.Canvas(holder, highlightthickness=0, borderwidth=0)
        scroll = ttk.Scrollbar(holder, orient="vertical", command=self._canvas.yview)
        self._inner = ttk.Frame(self._canvas)
        self._inner.bind(
            "<Configure>",
            lambda _e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._window = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")
        self._canvas.bind(
            "<Configure>",
            lambda e: self._canvas.itemconfigure(self._window, width=e.width))
        self._canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)
        self._render_sections()

    # ---------------------------------------------------------------- Aufbau
    def _render_sections(self) -> None:
        for child in self._inner.winfo_children():
            child.destroy()
        self._field_vars = {}
        snapshot = self.panel.render()
        status = snapshot.get("status", {})
        if status.get("status") == "blocked":
            keys = ", ".join(sorted({b.get("key", "?") for b in status.get("blockers", [])}))
            banner = tk.Label(self._inner, anchor="w", bg="#B91C1C", fg="#FFFFFF",
                              font=(FONT, 10, "bold"), padx=10, pady=6,
                              text=f"BLOCKED — Pflichtwerte fehlen oder sind ungültig: {keys}")
            banner.pack(fill="x", pady=(0, 8))
        for section in snapshot.get("sections", []):
            fields = section.get("fields", [])
            if not fields:
                continue
            box = ttk.LabelFrame(self._inner, text=section["title"], padding=10)
            box.pack(fill="x", pady=(0, 10), padx=(0, 4))
            box.columnconfigure(1, weight=1)
            row = 0
            for field in fields:
                label = field["key"] + (" *" if field.get("required") else "")
                ttk.Label(box, text=label).grid(row=row, column=0, sticky="w",
                                                padx=(0, 12), pady=(4, 0))
                widget = self._field_widget(box, field)
                widget.grid(row=row, column=1, sticky="ew", pady=(4, 0))
                origin = ORIGIN_LABELS.get(field.get("origin", ""), field.get("origin", ""))
                ttk.Label(box, text=origin, font=(FONT, 8)).grid(
                    row=row, column=2, sticky="e", padx=(12, 0), pady=(4, 0))
                if field.get("description"):
                    row += 1
                    ttk.Label(box, text=field["description"], font=(FONT, 8),
                              wraplength=720, justify="left").grid(
                        row=row, column=0, columnspan=3, sticky="w", pady=(0, 2))
                row += 1

    def _field_widget(self, parent: tk.Misc, field: dict[str, Any]) -> tk.Widget:
        key = field["key"]
        value = "" if field["value"] is None else str(field["value"])
        if field["type"] == "choice":
            var: Any = tk.StringVar(value=value or str(field.get("default", "")))
            widget: tk.Widget = ttk.Combobox(parent, textvariable=var, state="readonly",
                                             values=field.get("choices", []))
            self._field_vars[key] = ("choice", var)
            return widget
        if field["type"] == "bool":
            var = tk.BooleanVar(value=value.lower() in ("true", "1"))
            widget = ttk.Checkbutton(parent, variable=var)
            self._field_vars[key] = ("bool", var)
            return widget
        var = tk.StringVar(value=value)
        widget = ttk.Entry(parent, textvariable=var, show="•" if field.get("secret") else "")
        self._field_vars[key] = (field["type"], var)
        return widget

    # ---------------------------------------------------------------- Aktionen
    def save(self) -> dict[str, Any]:
        values = collect_values(self._field_vars)
        result = self.panel.save(values)
        if result.get("ok"):
            written = result.get("written", [])
            theme = values.get("SECONDBRAIN_GUI_THEME")
            if theme and "SECONDBRAIN_GUI_THEME" in written and self.on_theme_change:
                self.on_theme_change(theme)
            self._render_sections()
            self.result_var.set("Gespeichert: " + ", ".join(written) if written else "Keine Änderungen.")
        else:
            self.result_var.set("Fehler: " + " | ".join(result.get("errors", [])[:3]))
        return result

    def reload(self) -> None:
        self._render_sections()
        self.result_var.set("")


class SettingsWorkspaceFrame(SettingsEditorFrame):
    """MITTE-Zone der Desktop-Shell (Namenskonvention der übrigen Workspace-Panels)."""
