from __future__ import annotations

import json
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any

from secondbrain.native.actions import NativeActionDispatcher
from secondbrain.native.chat import NativeChatService
from secondbrain.native.runtime_snapshot import build_native_view_model
from secondbrain.native.voice_de import GermanVoiceCommandParser


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
    }

    def __init__(self, project_root: str | Path | None = None):
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.model = build_native_view_model(self.project_root)
        self.voice = GermanVoiceCommandParser()
        self.dispatcher = NativeActionDispatcher(self.project_root)
        self.chat_service = NativeChatService(self.project_root)
        self.root = tk.Tk()
        self.root.title("Jarvis / SecondBrain Agent")
        self.root.geometry("1220x790")
        self.root.minsize(1020, 660)
        self._tab_by_name: dict[str, tk.Widget] = {}
        self._build()

    def _build(self) -> None:
        self.root.configure(bg="#101820")
        header = ttk.Frame(self.root, padding=12)
        header.pack(fill="x")
        ttk.Label(header, text="Jarvis SecondBrain", font=("Segoe UI", 18, "bold")).pack(side="left")
        ttk.Label(header, text=f"v{self.model.get('version')} · Native Desktop · Deutsch", font=("Segoe UI", 10)).pack(side="left", padx=16)
        ttk.Button(header, text="Aktualisieren", command=self.refresh).pack(side="right")

        self.status_var = tk.StringVar(value=self._status_line())
        ttk.Label(self.root, textvariable=self.status_var, padding=(12, 4)).pack(fill="x")

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=12)
        self._add_dashboard_tab()
        self._add_chat_tab()
        self._add_documents_tab()
        self._add_memory_tab()
        self._add_rag_tab()
        self._add_voice_tab()
        self._add_audit_tab()
        self._add_settings_tab()
        self._add_developer_tab()

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
        return " | ".join([
            f"Bootstrap: {boot.get('status', 'unknown')}",
            f"RAG: {rag.get('status', 'unknown')}",
            f"Memory: {memory.get('status', 'unknown')}",
            f"Embedding: {provider.get('provider', 'unknown')}",
            f"Projekt: {self.project_root}",
        ])

    def _tree(self, parent: tk.Widget, payload: Any) -> tk.Text:
        text = tk.Text(parent, wrap="word", height=20)
        text.insert("1.0", json.dumps(payload, indent=2, ensure_ascii=False, default=str))
        text.configure(state="disabled")
        text.pack(fill="both", expand=True)
        return text

    def _add_dashboard_tab(self) -> None:
        frame = ttk.Frame(self.tabs, padding=12)
        self._add_tab("Dashboard", frame)
        cards = ttk.Frame(frame)
        cards.pack(fill="x", pady=(0, 10))
        values = [
            ("Modus", self.model.get("mode")),
            ("Web-HUD", self.model.get("web_hud")),
            ("Bootstrap", self.model.get("bootstrap", {}).get("status")),
            ("Provider", self.model.get("provider", {}).get("provider")),
            ("Sprache", self.model.get("voice", {}).get("language")),
            ("Aktionen", self.model.get("actions", {}).get("mode")),
        ]
        for title, value in values:
            box = ttk.LabelFrame(cards, text=title, padding=10)
            box.pack(side="left", fill="x", expand=True, padx=4)
            ttk.Label(box, text=str(value), font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self._tree(frame, {k: self.model[k] for k in ["bootstrap", "rag", "provider", "memory", "environment"] if k in self.model})


    def _add_chat_tab(self) -> None:
        frame = ttk.Frame(self.tabs, padding=12)
        self._add_tab("Chat", frame)
        ttk.Label(frame, text="Jarvis Chat Center: Fragen, RAG-Antworten und Verlauf", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        row = ttk.Frame(frame)
        row.pack(fill="x", pady=8)
        self.chat_input = tk.StringVar(value="Was ist der aktuelle Projektstatus?")
        ttk.Entry(row, textvariable=self.chat_input).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Fragen", command=self.chat_ask).pack(side="left", padx=4)
        ttk.Button(row, text="Suchen", command=self.chat_search).pack(side="left", padx=4)
        ttk.Button(row, text="Verlauf laden", command=self.chat_reload).pack(side="left", padx=4)
        self.chat_output = tk.Text(frame, wrap="word")
        self.chat_output.pack(fill="both", expand=True)
        self.chat_reload()

    def chat_ask(self) -> None:
        payload = self.chat_service.ask(self.chat_input.get())
        self._write_chat_output(payload)

    def chat_search(self) -> None:
        payload = self.chat_service.search(self.chat_input.get())
        self._write_chat_output(payload)

    def chat_reload(self) -> None:
        payload = self.chat_service.store.status(limit=30)
        self._write_chat_output(payload)

    def _write_chat_output(self, payload: dict[str, Any]) -> None:
        self.chat_output.configure(state="normal")
        self.chat_output.delete("1.0", "end")
        self.chat_output.insert("1.0", json.dumps(payload, indent=2, ensure_ascii=False, default=str))
        self.chat_output.configure(state="disabled")

    def _add_documents_tab(self) -> None:
        frame = ttk.Frame(self.tabs, padding=12)
        self._add_tab("Dokumente", frame)
        ttk.Label(frame, text="Document Center: Index, Chunks, Vectors, Parser-/OCR-Status", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self._tree(frame, self.model.get("rag", {}))

    def _add_memory_tab(self) -> None:
        frame = ttk.Frame(self.tabs, padding=12)
        self._add_tab("Gedächtnis", frame)
        ttk.Label(frame, text="Memory Center: Governance, Privacy, Lineage und deutsche Notizen", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self._tree(frame, self.model.get("memory", {}))

    def _add_rag_tab(self) -> None:
        frame = ttk.Frame(self.tabs, padding=12)
        self._add_tab("RAG / Produktion", frame)
        actions = self.model.get("p1_control", {}).get("groups", {})
        bar = ttk.Frame(frame)
        bar.pack(fill="x", pady=(0, 10))
        for group, items in actions.items():
            box = ttk.LabelFrame(bar, text=group, padding=8)
            box.pack(side="left", fill="both", expand=True, padx=3)
            for item in items[:4]:
                ttk.Label(box, text=f"• {item.get('title')}").pack(anchor="w")
        self._tree(frame, {"p1_control": self.model.get("p1_control"), "production": self.model.get("production"), "actions": self.model.get("actions")})

    def _add_voice_tab(self) -> None:
        frame = ttk.Frame(self.tabs, padding=12)
        self._add_tab("Sprache DE", frame)
        ttk.Label(frame, text="Deutsche Sprachsteuerung mit Action Bridge", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        row = ttk.Frame(frame)
        row.pack(fill="x", pady=8)
        self.voice_input = tk.StringVar(value="Jarvis Status")
        ttk.Entry(row, textvariable=self.voice_input).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Prüfen", command=self.parse_voice).pack(side="left", padx=4)
        ttk.Button(row, text="Ausführen", command=lambda: self.execute_voice(False)).pack(side="left", padx=4)
        ttk.Button(row, text="Bestätigt ausführen", command=lambda: self.execute_voice(True)).pack(side="left", padx=4)
        examples = ttk.LabelFrame(frame, text="Beispiele", padding=8)
        examples.pack(fill="x", pady=(0, 8))
        for item in self.model.get("voice", {}).get("examples", [])[:8]:
            ttk.Button(examples, text=item, command=lambda value=item: self._set_voice_example(value)).pack(side="left", padx=3, pady=2)
        self.voice_output = tk.Text(frame, height=12, wrap="word")
        self.voice_output.pack(fill="both", expand=True)
        self.voice_output.insert("1.0", json.dumps(self.model.get("voice"), indent=2, ensure_ascii=False))

    def _set_voice_example(self, value: str) -> None:
        self.voice_input.set(value)
        self.parse_voice()


    def _add_audit_tab(self) -> None:
        frame = ttk.Frame(self.tabs, padding=12)
        self._add_tab("Audit / Freigaben", frame)
        ttk.Label(frame, text="Action Audit und Freigabe-Warteschlange", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        bar = ttk.Frame(frame)
        bar.pack(fill="x", pady=8)
        ttk.Button(bar, text="Audit anzeigen", command=lambda: self._run_launcher("native-action-audit")).pack(side="left", padx=3)
        ttk.Button(bar, text="Offene Freigaben", command=lambda: self._run_launcher("native-approval-list")).pack(side="left", padx=3)
        self._tree(frame, self.model.get("audit", {}))

    def _add_settings_tab(self) -> None:
        frame = ttk.Frame(self.tabs, padding=12)
        self._add_tab("Einstellungen", frame)
        self._tree(frame, self.model.get("settings", {}))

    def _add_developer_tab(self) -> None:
        frame = ttk.Frame(self.tabs, padding=12)
        self._add_tab("Developer", frame)
        ttk.Button(frame, text="gui-bootstrap ausführen", command=lambda: self._run_launcher("gui-bootstrap")).pack(anchor="w", pady=3)
        ttk.Button(frame, text="p1-rag-status ausführen", command=lambda: self._run_launcher("p1-rag-status")).pack(anchor="w", pady=3)
        ttk.Button(frame, text="p1-production ausführen", command=lambda: self._run_launcher("p1-production")).pack(anchor="w", pady=3)
        ttk.Button(frame, text="native-action Jarvis Status", command=lambda: self._run_launcher("native-action", "Jarvis Status")).pack(anchor="w", pady=3)
        ttk.Button(frame, text="native-chat-status", command=lambda: self._run_launcher("native-chat-status")).pack(anchor="w", pady=3)
        ttk.Button(frame, text="native-action-audit", command=lambda: self._run_launcher("native-action-audit")).pack(anchor="w", pady=3)
        ttk.Button(frame, text="native-approval-list", command=lambda: self._run_launcher("native-approval-list")).pack(anchor="w", pady=3)
        self.developer_output = tk.Text(frame, wrap="word")
        self.developer_output.pack(fill="both", expand=True, pady=8)

    def parse_voice(self) -> None:
        intent = self.voice.parse(self.voice_input.get()).to_dict()
        self._write_voice_output(intent)

    def execute_voice(self, confirmed: bool = False) -> None:
        result = self.dispatcher.parse_and_dispatch(self.voice_input.get(), confirmed=confirmed).to_dict()
        self._write_voice_output(result)
        if result.get("next_view"):
            self._select_target(str(result["next_view"]))
        if result.get("status") == "confirmation_required":
            messagebox.showwarning("Bestätigung erforderlich", "Dieser Befehl verändert Daten. Nutze 'Bestätigt ausführen'.")

    def _write_voice_output(self, payload: dict[str, Any]) -> None:
        self.voice_output.configure(state="normal")
        self.voice_output.delete("1.0", "end")
        self.voice_output.insert("1.0", json.dumps(payload, indent=2, ensure_ascii=False, default=str))
        self.voice_output.configure(state="disabled")

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
        self.developer_output.delete("1.0", "end")
        self.developer_output.insert("1.0", body)

    def refresh(self) -> None:
        self.model = build_native_view_model(self.project_root)
        self.status_var.set(self._status_line())
        messagebox.showinfo("Jarvis", "Runtime-Status aktualisiert.")

    def run(self) -> int:
        self.root.mainloop()
        return 0


def build_native_view_model(root: str | Path | None = None) -> dict[str, Any]:
    from secondbrain.native.runtime_snapshot import build_native_view_model as build
    return build(root)


def run_native_app(project_root: str | Path | None = None) -> int:
    app = NativeJarvisApp(project_root)
    return app.run()
