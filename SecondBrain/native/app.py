"""Native Tkinter-Desktop-App (Jarvis) — v2-Oberfläche.

- Theme (dark/light) über secondbrain.ui-Tokens, umschaltbar in den Einstellungen
- Strukturierte Baumansichten statt JSON-Dumps in allen Tabs
- Einstellungen: editierbar, in Bereiche gegliedert, über die zentrale RuntimeConfig
  (Nicht-Secrets -> config.json, Secrets -> .env; identisch mit der CLI)
- BLOCKED-Banner, wenn die Startvalidierung Pflichtwerte vermisst
"""

from __future__ import annotations

import json
import subprocess
import sys
import tkinter as tk
from datetime import datetime, timezone
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any

from secondbrain.native.actions import NativeActionDispatcher
from secondbrain.native.chat import ChatEngine
from secondbrain.native.runtime_snapshot import build_native_view_model
from secondbrain.native.settings_panel import NativeSettingsPanel
from secondbrain.native.voice_de import GermanVoiceCommandParser
from secondbrain.ui.theme import ThemeRegistry, ttk_style_map
from secondbrain.ui import tokens

FONT = tokens.FONT_FAMILY


class NativeJarvisApp:
    """Eigenständige Tkinter-Desktop-App mit deutscher Action-Ausführung."""

    TAB_TARGETS = {
        "dashboard": "Dashboard",
        "documents": "Dokumente",
        "chat": "Chat",
        "memory": "Gedächtnis",
        "rag": "RAG / Produktion",
        "search": "RAG / Produktion",
        "settings": "Einstellungen",
        "status": "Dashboard",
        "jobs": "Developer",
        "audit": "Audit / Freigaben",
    }

    def __init__(self, project_root: str | Path | None = None):
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.model = build_native_view_model(self.project_root)
        self.voice = GermanVoiceCommandParser()
        self.dispatcher = NativeActionDispatcher(self.project_root)
        self.chat_service = ChatEngine(self.project_root)
        self.settings_panel = NativeSettingsPanel(self.project_root)
        self.themes = ThemeRegistry(self._configured_theme())
        self.root = tk.Tk()
        self.root.title("Jarvis / SecondBrain Agent")
        self.root.geometry("1280x820")
        self.root.minsize(1040, 680)
        self._tab_by_name: dict[str, tk.Widget] = {}
        self._texts: list[tk.Text] = []
        self._build()

    # ------------------------------------------------------------------ Theme
    def _configured_theme(self) -> str:
        try:
            name = self.settings_panel.config.get("SECONDBRAIN_GUI_THEME")
        except Exception:
            name = "dark"
        return name if name in ("dark", "light") else "dark"

    def _apply_theme(self, name: str | None = None) -> None:
        theme = self.themes.set(name) if name else self.themes.active()
        p = theme.palette
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        for style_name, opts in ttk_style_map(theme).items():
            if style_name == "focus":
                continue
            style.configure(style_name, **opts)
        style.configure("TNotebook", background=p["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=p["surface_alt"], foreground=p["fg"],
                        padding=(tokens.SPACING["md"], tokens.SPACING["sm"]))
        style.map("TNotebook.Tab",
                  background=[("selected", p["primary"])],
                  foreground=[("selected", p["on_primary"])])
        style.configure("Treeview", background=p["surface"], fieldbackground=p["surface"],
                        foreground=p["fg"], borderwidth=0, rowheight=22)
        style.configure("Treeview.Heading", background=p["surface_alt"], foreground=p["fg"])
        style.configure("TLabelframe", background=p["bg"], foreground=p["fg"], bordercolor=p["border"])
        style.configure("TLabelframe.Label", background=p["bg"], foreground=p["fg_muted"])
        style.configure("TEntry", fieldbackground=p["surface_alt"], foreground=p["fg"],
                        insertcolor=p["fg"], bordercolor=p["border"])
        style.configure("TCombobox", fieldbackground=p["surface_alt"], foreground=p["fg"],
                        background=p["surface_alt"], arrowcolor=p["fg"])
        style.configure("TCheckbutton", background=p["bg"], foreground=p["fg"])
        style.map("TCheckbutton", background=[("active", p["bg"])])
        style.configure("Card.TLabelframe", background=p["surface"], bordercolor=p["border"])
        style.configure("Card.TLabelframe.Label", background=p["surface"], foreground=p["fg_muted"])
        style.configure("CardValue.TLabel", background=p["surface"], foreground=p["fg"],
                        font=(FONT, tokens.FONT_SIZES["subtitle"], "bold"))
        style.configure("Blocked.TLabel", background=p["error"], foreground="#FFFFFF",
                        font=(FONT, tokens.FONT_SIZES["body"], "bold"),
                        padding=(tokens.SPACING["md"], tokens.SPACING["sm"]))
        style.configure("Ok.TLabel", background=p["success"], foreground="#04222A",
                        font=(FONT, tokens.FONT_SIZES["body"], "bold"),
                        padding=(tokens.SPACING["md"], tokens.SPACING["sm"]))
        self.root.configure(bg=p["bg"])
        for text in self._texts:
            try:
                text.configure(bg=p["surface"], fg=p["fg"], insertbackground=p["fg"],
                               selectbackground=p["primary"], selectforeground=p["on_primary"],
                               relief="flat", highlightthickness=1,
                               highlightbackground=p["border"], highlightcolor=p["focus"])
            except tk.TclError:
                pass

    # ------------------------------------------------------------------ Aufbau
    def _build(self) -> None:
        header = ttk.Frame(self.root, padding=(12, 10))
        header.pack(fill="x")
        ttk.Label(header, text="Jarvis SecondBrain",
                  font=(FONT, tokens.FONT_SIZES["title"], "bold")).pack(side="left")
        ttk.Label(header, text=f"v{self.model.get('version')} · Native Desktop · Deutsch",
                  style="Muted.TLabel", font=(FONT, tokens.FONT_SIZES["caption"])).pack(side="left", padx=16)
        ttk.Button(header, text="Aktualisieren", command=self.refresh).pack(side="right", padx=(4, 0))
        ttk.Button(header, text="Theme wechseln", command=self.toggle_theme).pack(side="right")

        self.config_banner = ttk.Label(self.root, text="", anchor="w")
        self.config_banner.pack(fill="x", padx=12)
        self.status_var = tk.StringVar(value=self._status_line())
        ttk.Label(self.root, textvariable=self.status_var, style="Muted.TLabel",
                  padding=(12, 4)).pack(fill="x")

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        self._add_dashboard_tab()
        self._add_chat_tab()
        self._add_documents_tab()
        self._add_memory_tab()
        self._add_rag_tab()
        self._add_voice_tab()
        self._add_audit_tab()
        self._add_settings_tab()
        self._add_developer_tab()
        self._apply_theme()
        self._update_config_banner()

    def _add_tab(self, name: str, frame: ttk.Frame) -> None:
        self.tabs.add(frame, text=name)
        self._tab_by_name[name] = frame

    def _select_target(self, target: str) -> None:
        name = self.TAB_TARGETS.get(target, "Dashboard")
        frame = self._tab_by_name.get(name)
        if frame is not None:
            self.tabs.select(frame)

    def _status_line(self) -> str:
        boot = self.model.get("bootstrap", {})
        rag = self.model.get("rag", {})
        provider = self.model.get("provider", {})
        memory = self.model.get("memory", {})
        config = self.model.get("config_status", {})
        return "  |  ".join([
            f"Konfiguration: {str(config.get('status', 'unbekannt')).upper()}",
            f"Bootstrap: {boot.get('status', 'unknown')}",
            f"RAG: {rag.get('status', 'unknown')}",
            f"Memory: {memory.get('status', 'unknown')}",
            f"Embedding: {provider.get('provider', 'unknown')}",
            f"Projekt: {self.project_root}",
        ])

    def _update_config_banner(self) -> None:
        config = self.model.get("config_status", {})
        blockers = config.get("blockers", [])
        if config.get("status") == "blocked":
            keys = ", ".join(sorted({b.get("key", "?") for b in blockers}))
            self.config_banner.configure(
                text=f"  Konfiguration BLOCKED — fehlende/ungültige Pflichtwerte: {keys}. "
                     "Behebung im Tab 'Einstellungen'.",
                style="Blocked.TLabel")
        else:
            self.config_banner.configure(text="  Konfiguration OK", style="Ok.TLabel")

    # ---------------------------------------------------------- Basisbausteine
    def _make_text(self, parent: tk.Widget, height: int = 12) -> tk.Text:
        text = tk.Text(parent, wrap="word", height=height, font=(FONT, tokens.FONT_SIZES["body"]))
        self._texts.append(text)
        return text

    def _kv_tree(self, parent: tk.Widget, payload: Any, expand_levels: int = 1) -> ttk.Treeview:
        """Strukturierte Schlüssel/Wert-Baumansicht für verschachtelte Dicts/Listen."""
        holder = ttk.Frame(parent)
        holder.pack(fill="both", expand=True)
        tree = ttk.Treeview(holder, columns=("wert",), show="tree headings")
        tree.heading("#0", text="Schlüssel")
        tree.heading("wert", text="Wert")
        tree.column("#0", width=340, stretch=False)
        tree.column("wert", stretch=True)
        scroll = ttk.Scrollbar(holder, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)

        def insert(parent_id: str, key: str, value: Any, level: int) -> None:
            if isinstance(value, dict):
                node = tree.insert(parent_id, "end", text=str(key), values=("",),
                                   open=level < expand_levels)
                for sub_key, sub_value in value.items():
                    insert(node, str(sub_key), sub_value, level + 1)
            elif isinstance(value, (list, tuple)):
                node = tree.insert(parent_id, "end", text=str(key),
                                   values=(f"{len(value)} Einträge",), open=level < expand_levels)
                for index, item in enumerate(value):
                    insert(node, f"[{index}]", item, level + 1)
            else:
                rendered = "" if value is None else str(value)
                tree.insert(parent_id, "end", text=str(key), values=(rendered,))

        if isinstance(payload, dict):
            for key, value in payload.items():
                insert("", str(key), value, 0)
        else:
            insert("", "wert", payload, 0)
        return tree

    def _card_row(self, parent: tk.Widget, values: list[tuple[str, Any]]) -> None:
        cards = ttk.Frame(parent)
        cards.pack(fill="x", pady=(0, 10))
        for title, value in values:
            box = ttk.LabelFrame(cards, text=title, padding=10, style="Card.TLabelframe")
            box.pack(side="left", fill="x", expand=True, padx=4)
            ttk.Label(box, text=str(value), style="CardValue.TLabel").pack(anchor="w")

    # ------------------------------------------------------------------- Tabs
    def _add_dashboard_tab(self) -> None:
        frame = ttk.Frame(self.tabs, padding=12)
        self._add_tab("Dashboard", frame)
        config = self.model.get("config_status", {})
        self._card_row(frame, [
            ("Modus", self.model.get("mode")),
            ("Konfiguration", str(config.get("status", "?")).upper()),
            ("Bootstrap", self.model.get("bootstrap", {}).get("status")),
            ("Provider", self.model.get("provider", {}).get("provider")),
            ("Sprache", self.model.get("voice", {}).get("language")),
            ("Aktionen", self.model.get("actions", {}).get("mode")),
        ])
        self._kv_tree(frame, {k: self.model[k] for k in
                              ["bootstrap", "rag", "provider", "memory", "environment", "config_status"]
                              if k in self.model})

    def _add_chat_tab(self) -> None:
        frame = ttk.Frame(self.tabs, padding=12)
        self._add_tab("Chat", frame)
        ttk.Label(frame, text="Jarvis Chat Center: Fragen, RAG-Antworten und Verlauf",
                  font=(FONT, tokens.FONT_SIZES["subtitle"], "bold")).pack(anchor="w")
        row = ttk.Frame(frame)
        row.pack(fill="x", pady=8)
        self.chat_input = tk.StringVar(value="Was ist der aktuelle Projektstatus?")
        entry = ttk.Entry(row, textvariable=self.chat_input)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda _e: self.chat_ask())
        ttk.Button(row, text="Fragen", style="Primary.TButton", command=self.chat_ask).pack(side="left", padx=4)
        ttk.Button(row, text="Suchen", command=self.chat_search).pack(side="left", padx=4)
        ttk.Button(row, text="Verlauf laden", command=self.chat_reload).pack(side="left", padx=4)
        self.chat_output = self._make_text(frame)
        self.chat_output.pack(fill="both", expand=True)
        self.chat_reload()

    def chat_ask(self) -> None:
        self._write_chat_output(self.chat_service.ask(self.chat_input.get()))

    def chat_search(self) -> None:
        self._write_chat_output(self.chat_service.search(self.chat_input.get()))

    def chat_reload(self) -> None:
        self._write_chat_output(self.chat_service.store.status(limit=30))

    def _write_chat_output(self, payload: dict[str, Any]) -> None:
        self.chat_output.configure(state="normal")
        self.chat_output.delete("1.0", "end")
        answer = payload.get("answer") if isinstance(payload, dict) else None
        if isinstance(answer, str) and answer.strip():
            sources = payload.get("sources") or payload.get("citations") or []
            body = answer.strip()
            if sources:
                body += "\n\nQuellen:\n" + "\n".join(f"  - {s}" for s in sources[:8])
            self.chat_output.insert("1.0", body)
        else:
            self.chat_output.insert("1.0", json.dumps(payload, indent=2, ensure_ascii=False, default=str))
        self.chat_output.configure(state="disabled")

    def _add_documents_tab(self) -> None:
        frame = ttk.Frame(self.tabs, padding=12)
        self._add_tab("Dokumente", frame)
        ttk.Label(frame, text="Document Center: Index, Chunks, Vectors, Parser-/OCR-Status",
                  font=(FONT, tokens.FONT_SIZES["subtitle"], "bold")).pack(anchor="w", pady=(0, 8))
        self._kv_tree(frame, self.model.get("rag", {}))

    def _add_memory_tab(self) -> None:
        frame = ttk.Frame(self.tabs, padding=12)
        self._add_tab("Gedächtnis", frame)
        ttk.Label(frame, text="Memory Center: Governance, Privacy, Lineage und deutsche Notizen",
                  font=(FONT, tokens.FONT_SIZES["subtitle"], "bold")).pack(anchor="w", pady=(0, 8))
        self._kv_tree(frame, self.model.get("memory", {}))

    def _add_rag_tab(self) -> None:
        frame = ttk.Frame(self.tabs, padding=12)
        self._add_tab("RAG / Produktion", frame)
        actions = self.model.get("p1_control", {}).get("groups", {})
        if actions:
            bar = ttk.Frame(frame)
            bar.pack(fill="x", pady=(0, 10))
            for group, items in actions.items():
                box = ttk.LabelFrame(bar, text=group, padding=8, style="Card.TLabelframe")
                box.pack(side="left", fill="both", expand=True, padx=3)
                for item in items[:4]:
                    ttk.Label(box, text=f"• {item.get('title')}", style="Muted.TLabel").pack(anchor="w")
        self._kv_tree(frame, {
            "p1_control": self.model.get("p1_control"),
            "production": self.model.get("production"),
            "actions": self.model.get("actions"),
        })

    def _add_voice_tab(self) -> None:
        frame = ttk.Frame(self.tabs, padding=12)
        self._add_tab("Sprache DE", frame)
        ttk.Label(frame, text="Deutsche Sprachsteuerung mit Action Bridge",
                  font=(FONT, tokens.FONT_SIZES["subtitle"], "bold")).pack(anchor="w")
        row = ttk.Frame(frame)
        row.pack(fill="x", pady=8)
        self.voice_input = tk.StringVar(value="Jarvis Status")
        ttk.Entry(row, textvariable=self.voice_input).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Prüfen", command=self.parse_voice).pack(side="left", padx=4)
        ttk.Button(row, text="Ausführen", command=lambda: self.execute_voice(False)).pack(side="left", padx=4)
        ttk.Button(row, text="Bestätigt ausführen", style="Primary.TButton",
                   command=lambda: self.execute_voice(True)).pack(side="left", padx=4)
        examples = ttk.LabelFrame(frame, text="Beispiele", padding=8)
        examples.pack(fill="x", pady=(0, 8))
        for item in self.model.get("voice", {}).get("examples", [])[:8]:
            ttk.Button(examples, text=item,
                       command=lambda value=item: self._set_voice_example(value)).pack(side="left", padx=3, pady=2)
        self.voice_output = self._make_text(frame, height=12)
        self.voice_output.pack(fill="both", expand=True)
        self.voice_output.insert("1.0", json.dumps(self.model.get("voice"), indent=2, ensure_ascii=False))

    def _set_voice_example(self, value: str) -> None:
        self.voice_input.set(value)
        self.parse_voice()

    def _add_audit_tab(self) -> None:
        frame = ttk.Frame(self.tabs, padding=12)
        self._add_tab("Audit / Freigaben", frame)
        ttk.Label(frame, text="Action Audit und Freigabe-Warteschlange",
                  font=(FONT, tokens.FONT_SIZES["subtitle"], "bold")).pack(anchor="w")
        bar = ttk.Frame(frame)
        bar.pack(fill="x", pady=8)
        ttk.Button(bar, text="Audit anzeigen",
                   command=lambda: self._run_launcher("native-action-audit")).pack(side="left", padx=3)
        ttk.Button(bar, text="Offene Freigaben",
                   command=lambda: self._run_launcher("native-approval-list")).pack(side="left", padx=3)
        ttk.Button(bar, text="Export als JSON", command=self.export_audit_json).pack(side="left", padx=3)
        self.audit_export_var = tk.StringVar(value="")
        ttk.Label(bar, textvariable=self.audit_export_var, style="Muted.TLabel").pack(side="left", padx=8)
        self._kv_tree(frame, self.model.get("audit", {}))

    def export_audit_json(self) -> None:
        target_dir = self.project_root / "runtime" / "exports"
        target_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        target = target_dir / f"audit_export_{stamp}.json"
        target.write_text(json.dumps(self.model.get("audit", {}), indent=2,
                                     ensure_ascii=False, default=str), encoding="utf-8")
        self.audit_export_var.set(f"exportiert: {target}")

    # ------------------------------------------------------------ Einstellungen
    def _add_settings_tab(self) -> None:
        frame = ttk.Frame(self.tabs, padding=12)
        self._add_tab("Einstellungen", frame)
        from secondbrain.native.settings_workspace_panel import SettingsEditorFrame
        self.settings_editor = SettingsEditorFrame(
            frame, self.project_root, on_theme_change=self._on_settings_theme_change)
        self.settings_editor.pack(fill="both", expand=True)

    def _on_settings_theme_change(self, theme: str) -> None:
        self._apply_theme(theme)
        self.refresh(silent=True)

    # ---------------------------------------------------------------- Developer
    def _add_developer_tab(self) -> None:
        frame = ttk.Frame(self.tabs, padding=12)
        self._add_tab("Developer", frame)
        bar = ttk.Frame(frame)
        bar.pack(fill="x")
        commands = [
            ("config-doctor", ("config-doctor",)),
            ("config-status", ("config-status",)),
            ("gui-bootstrap", ("gui-bootstrap",)),
            ("p1-rag-status", ("p1-rag-status",)),
            ("p1-production", ("p1-production",)),
            ("native-chat-status", ("native-chat-status",)),
            ("native-action-audit", ("native-action-audit",)),
            ("native-approval-list", ("native-approval-list",)),
        ]
        for column, (label, args) in enumerate(commands):
            ttk.Button(bar, text=label,
                       command=lambda a=args: self._run_launcher(*a)).grid(
                row=column // 4, column=column % 4, sticky="w", padx=3, pady=3)
        self.developer_output = self._make_text(frame)
        self.developer_output.pack(fill="both", expand=True, pady=8)

    # ------------------------------------------------------------------- Voice
    def parse_voice(self) -> None:
        self._write_voice_output(self.voice.parse(self.voice_input.get()).to_dict())

    def execute_voice(self, confirmed: bool = False) -> None:
        result = self.dispatcher.parse_and_dispatch(self.voice_input.get(), confirmed=confirmed).to_dict()
        self._write_voice_output(result)
        if result.get("next_view"):
            self._select_target(str(result["next_view"]))
        if result.get("status") == "confirmation_required":
            messagebox.showwarning("Bestätigung erforderlich",
                                   "Dieser Befehl verändert Daten. Nutze 'Bestätigt ausführen'.")

    def _write_voice_output(self, payload: dict[str, Any]) -> None:
        self.voice_output.configure(state="normal")
        self.voice_output.delete("1.0", "end")
        self.voice_output.insert("1.0", json.dumps(payload, indent=2, ensure_ascii=False, default=str))
        self.voice_output.configure(state="disabled")

    # ----------------------------------------------------------------- Runtime
    def _run_launcher(self, command: str, *extra: str) -> None:
        try:
            proc = subprocess.run(
                [sys.executable, "launcher.py", command, *extra],
                cwd=str(self.project_root),
                text=True,
                capture_output=True,
                timeout=30,
            )
            body = proc.stdout or proc.stderr or f"returncode={proc.returncode}"
        except Exception as exc:
            body = f"{type(exc).__name__}: {exc}"
        self.developer_output.configure(state="normal")
        self.developer_output.delete("1.0", "end")
        self.developer_output.insert("1.0", body)

    def toggle_theme(self) -> None:
        theme = self.themes.toggle()
        self._apply_theme()
        self.settings_panel.save({"SECONDBRAIN_GUI_THEME": theme.name})
        if hasattr(self, "settings_editor"):
            self.settings_editor.reload()

    def refresh(self, silent: bool = False) -> None:
        self.model = build_native_view_model(self.project_root)
        self.status_var.set(self._status_line())
        self._update_config_banner()
        if not silent:
            messagebox.showinfo("Jarvis", "Runtime-Status aktualisiert.")

    def run(self) -> int:
        self.root.mainloop()
        return 0


def build_native_view_model_compat(root: str | Path | None = None) -> dict[str, Any]:
    from secondbrain.native.runtime_snapshot import build_native_view_model as build
    return build(root)


def run_native_app(project_root: str | Path | None = None) -> int:
    app = NativeJarvisApp(project_root)
    return app.run()
