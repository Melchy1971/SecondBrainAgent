from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Any

from secondbrain.chat import ChatService, CitationRenderer, MarkdownRenderer
from secondbrain.native.layout_center.service import NativeLayoutService
from secondbrain.native.theme_center.service import ThemeCenterService

from .models import ApplicationState
from .service import AIWorkspaceService


class AIChatWorkspaceFrame(ttk.Frame):
    SOURCES = ("documents", "folders", "ocr", "memory", "github", "mail", "csv")

    def __init__(self, master: tk.Misc, state: ApplicationState, project_root: Path, navigate_callback: Any = None) -> None:
        super().__init__(master)
        self.state = state
        self.project_root = project_root
        self.navigate_callback = navigate_callback
        self.service = ChatService(project_root)
        self.stream = self.service.stream_manager
        self.renderer = MarkdownRenderer()
        self.citation_renderer = CitationRenderer()
        self.last_prompt = ""
        self.source_vars = {source: tk.BooleanVar(value=source in {"documents", "memory"}) for source in self.SOURCES}
        self.provider_var = tk.StringVar(value=state.active_provider)
        self.model_var = tk.StringVar(value=state.active_model)
        self.prompt_var = tk.StringVar()
        self._build()
        self.reload_conversation()

    def _build(self) -> None:
        panes = ttk.PanedWindow(self, orient="horizontal")
        panes.pack(fill="both", expand=True)
        left = ttk.Frame(panes, padding=8)
        center = ttk.Frame(panes, padding=8)
        right = ttk.Frame(panes, padding=8)
        panes.add(left, weight=1)
        panes.add(center, weight=4)
        panes.add(right, weight=2)

        ttk.Label(left, text="Document Context", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        for source in self.SOURCES:
            ttk.Checkbutton(left, text=source.title(), variable=self.source_vars[source]).pack(anchor="w", pady=2)
        ttk.Separator(left).pack(fill="x", pady=8)
        ttk.Button(left, text="Datei anhaengen", command=self.attach_file).pack(fill="x")
        self.attachment_label = ttk.Label(left, text="Keine Attachments", wraplength=180)
        self.attachment_label.pack(fill="x", pady=8)

        provider_row = ttk.Frame(center)
        provider_row.pack(fill="x", pady=(0, 6))
        ttk.Label(provider_row, text="Provider").pack(side="left")
        ttk.Combobox(provider_row, textvariable=self.provider_var, values=("openai", "ollama", "gemini", "claude"), state="readonly", width=12).pack(side="left", padx=4)
        ttk.Label(provider_row, text="Model").pack(side="left", padx=(8, 0))
        ttk.Entry(provider_row, textvariable=self.model_var).pack(side="left", fill="x", expand=True, padx=4)

        self.transcript = tk.Text(center, wrap="word", state="disabled")
        self.transcript.pack(fill="both", expand=True)
        input_row = ttk.Frame(center)
        input_row.pack(fill="x", pady=(6, 0))
        ttk.Entry(input_row, textvariable=self.prompt_var).pack(side="left", fill="x", expand=True)
        ttk.Button(input_row, text="Start", command=self.start).pack(side="left", padx=3)
        ttk.Button(input_row, text="Cancel", command=self.cancel).pack(side="left", padx=3)
        ttk.Button(input_row, text="Retry", command=self.retry).pack(side="left", padx=3)
        ttk.Button(input_row, text="Continue", command=self.continue_response).pack(side="left", padx=3)

        ttk.Label(right, text="Citations", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        columns = ("chunk", "score", "workspace", "source", "provider")
        self.citations = ttk.Treeview(right, columns=columns, show="tree headings")
        self.citations.heading("#0", text="Dokument")
        for column in columns:
            self.citations.heading(column, text=column.title())
            self.citations.column(column, width=80)
        self.citations.pack(fill="both", expand=True)
        self.citations.bind("<Double-1>", self.open_citation)

    def selected_sources(self) -> list[str]:
        return [source for source, variable in self.source_vars.items() if variable.get()]

    def start(self) -> None:
        prompt = self.prompt_var.get().strip()
        if not prompt:
            return
        self.last_prompt = prompt
        self.prompt_var.set("")
        self.state.active_provider = self.provider_var.get()
        self.state.active_model = self.model_var.get()
        self._start_stream(prompt)

    def _start_stream(self, prompt: str) -> None:
        try:
            self.service.stream(
                prompt,
                conversation_id=self.state.current_conversation,
                provider=self.provider_var.get(),
                model=self.model_var.get(),
                selected_sources=self.selected_sources(),
                selected_documents=self.state.selected_documents,
                on_chunk=lambda _chunk: self.after(0, self._render_stream),
                on_done=lambda _content, _cancelled: self.after(0, self._stream_done),
                on_error=lambda exc: self.after(0, lambda: self._show_error(exc)),
            )
        except RuntimeError:
            return
        self.state.status = "streaming"
        self.state.message = "Antwort wird gestreamt"

    def cancel(self) -> None:
        self.service.cancel()

    def retry(self) -> None:
        if self.last_prompt:
            self._start_stream(self.last_prompt)

    def continue_response(self) -> None:
        self.last_prompt = "Bitte setze die letzte Antwort fort."
        self._start_stream(self.last_prompt)

    def _render_stream(self) -> None:
        self.renderer.render_into(self.transcript, self.stream.content())

    def _stream_done(self) -> None:
        if self.service.last_conversation_id:
            self.state.current_conversation = self.service.last_conversation_id
        self.state.status = "ready"
        self.state.message = "Antwort abgeschlossen"
        self.reload_conversation()

    def reload_conversation(self) -> None:
        messages = self.service.conversations.messages(self.state.current_conversation) if self.state.current_conversation else []
        markdown = "\n\n".join(f"## {str(row.get('role', '')).title()}\n\n{row.get('content', '')}" for row in messages)
        self.renderer.render_into(self.transcript, markdown)
        latest = next((row for row in reversed(messages) if row.get("role") == "assistant"), None)
        citations = list((latest or {}).get("metadata", {}).get("citations", []))
        self._render_citations(citations)
        if self.state.current_conversation:
            attachments = self.service.attachments.list(self.state.current_conversation)
            self.attachment_label.configure(text=f"Attachments: {len(attachments)}")

    def _render_citations(self, rows: list[dict[str, Any]]) -> None:
        for item in self.citations.get_children():
            self.citations.delete(item)
        for row in self.citation_renderer.rows(rows):
            self.citations.insert("", "end", iid=row["iid"], text=row["document"], values=row["values"], tags=(row["tag"],))

    def open_citation(self, _event: object | None = None) -> None:
        selected = self.citations.selection()
        if not selected:
            return
        tags = self.citations.item(selected[0], "tags")
        if tags:
            self.state.selected_documents = [str(tags[0])]
            self.state.active_workspace = "documents"
            self.state.message = f"Quelle ausgewaehlt: {tags[0]}"
            if self.navigate_callback is not None:
                self.navigate_callback("documents")

    def attach_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Supported", "*.pdf *.docx *.xlsx *.csv *.txt *.png *.jpg *.jpeg *.json *.md")])
        if not path:
            return
        if self.state.current_conversation is None:
            conversation = self.service.conversations.create("Attachments", provider=self.provider_var.get(), model=self.model_var.get())
            self.state.current_conversation = str(conversation["id"])
        result = self.service.attachments.attach(self.state.current_conversation, path)
        self.state.message = result.get("status", "attachment")
        if result.get("ok") and result.get("path"):
            self.state.selected_documents = [str(result["path"])]
        self.reload_conversation()

    def _show_error(self, exc: Exception) -> None:
        self.state.set_error(f"{type(exc).__name__}: {exc}")


class AIWorkspaceApp(tk.Tk):
    """Shared native shell for all desktop modules."""

    def __init__(self, project_root: str | Path = ".", initial_module: str = "chat") -> None:
        super().__init__()
        self.project_root = Path(project_root).resolve()
        self.service = AIWorkspaceService(self.project_root)
        self.theme_service = ThemeCenterService(self.project_root)
        self.layout_service = NativeLayoutService(self.project_root)
        self.state: ApplicationState = self.service.application_state()
        self.state.active_module = initial_module
        self.state.active_workspace = initial_module
        self.title("Jarvis - Native Desktop")
        self.geometry("1240x780")
        self.minsize(960, 620)
        self._build_shell()
        self.refresh()

    def _build_shell(self) -> None:
        theme = self.theme_service.current_theme().tokens
        background = theme.get("background", "#0F172A")
        foreground = theme.get("foreground", "#E5E7EB")
        self.configure(bg=background)

        header = tk.Frame(self, bg=background)
        header.pack(fill="x", padx=14, pady=(12, 6))
        tk.Label(
            header,
            text="Jarvis Native Desktop",
            bg=background,
            fg=foreground,
            font=("Segoe UI", 20, "bold"),
        ).pack(side="left")
        self.version_label = tk.Label(header, bg=background, fg=foreground)
        self.version_label.pack(side="left", padx=14)

        self.toolbar = ttk.Frame(self, padding=(14, 4))
        self.toolbar.pack(fill="x")
        ttk.Button(self.toolbar, text="Dashboard", command=lambda: self.navigate("dashboard")).pack(side="left")
        ttk.Button(self.toolbar, text="Zurueck", command=self.navigate_back).pack(side="left", padx=6)
        ttk.Button(self.toolbar, text="Aktualisieren", command=self.refresh).pack(side="left")
        self.module_title = ttk.Label(self.toolbar, text="", font=("Segoe UI", 11, "bold"))
        self.module_title.pack(side="right")

        layout = self.layout_service.load()["layout"]
        body = tk.PanedWindow(self, orient="horizontal", bg=background, sashwidth=4)
        body.pack(fill="both", expand=True, padx=14, pady=8)
        navigation_frame = ttk.Frame(body, padding=8)
        content_frame = ttk.Frame(body, padding=8)
        body.add(navigation_frame, width=layout.get("left_width", 260))
        body.add(content_frame)

        self.navigation = ttk.Treeview(navigation_frame, columns=("status",), show="tree headings", selectmode="browse")
        self.navigation.heading("#0", text="Modul")
        self.navigation.heading("status", text="Status")
        self.navigation.column("#0", width=185)
        self.navigation.column("status", width=70, anchor="center")
        self.navigation.pack(fill="both", expand=True)
        self.navigation.bind("<<TreeviewSelect>>", self._on_navigation)

        self.content_frame = content_frame
        self.detail = tk.Text(content_frame, wrap="word", borderwidth=0)
        self.detail.pack(fill="both", expand=True)
        self.chat_workspace = AIChatWorkspaceFrame(content_frame, self.state, self.project_root, self.navigate)

        self.status_text = tk.StringVar(value="Desktop wird initialisiert")
        self.statusbar = ttk.Label(self, textvariable=self.status_text, relief="sunken", anchor="w", padding=(8, 4))
        self.statusbar.pack(fill="x", side="bottom")

    def refresh(self) -> None:
        snapshot = self.service.snapshot()
        self.state.version = snapshot.version
        self.state.replace_modules(snapshot.modules)
        self.version_label.configure(text=self.state.version)
        current_selection = self.state.active_module
        for item in self.navigation.get_children():
            self.navigation.delete(item)
        for module in self.state.modules:
            self.navigation.insert("", "end", iid=module.id, text=module.title, values=(module.status,))
        if current_selection and self.navigation.exists(current_selection):
            self.navigation.selection_set(current_selection)
            self.navigation.focus(current_selection)
        self._render_active_module()

    def navigate(self, module_id: str) -> None:
        try:
            self.state.select_module(module_id)
        except (KeyError, ValueError) as exc:
            self.state.set_error(str(exc))
            self._update_status()
            return
        if self.navigation.exists(module_id):
            self.navigation.selection_set(module_id)
            self.navigation.focus(module_id)
        self._render_active_module()

    def navigate_back(self) -> None:
        self.navigate("dashboard")

    def _on_navigation(self, _event: object | None = None) -> None:
        selected = self.navigation.selection()
        if selected and selected[0] != self.state.active_module:
            self.navigate(selected[0])

    def _render_active_module(self) -> None:
        module = next((item for item in self.state.modules if item.id == self.state.active_module), None)
        if module is None:
            self._show({"ok": False, "status": "no_active_module"})
            self._update_status()
            return
        if module.id == "chat":
            self.detail.pack_forget()
            self.chat_workspace.pack(fill="both", expand=True)
            self.chat_workspace.reload_conversation()
            self.state.status = "ready"
            self.state.message = "AI Chat Workspace bereit"
            self.module_title.configure(text=module.title)
            self._update_status()
            return
        self.chat_workspace.pack_forget()
        self.detail.pack(fill="both", expand=True)
        payload = self.service.module_payload(module.id)
        if payload.get("status") == "module_error":
            self.state.set_error(f"{module.title}: {payload.get('status', 'Fehler')}")
        elif not payload.get("ok", False):
            self.state.status = "degraded"
            self.state.message = f"{module.title} eingeschraenkt"
            self.state.touch()
        else:
            self.state.status = "ready"
            self.state.message = f"{module.title} bereit"
            self.state.touch()
        self.module_title.configure(text=module.title)
        self._show({"module": module.to_dict(), "data": payload})
        self._update_status()

    def _update_status(self) -> None:
        self.status_text.set(
            f"{self.state.status.upper()} | {self.state.message} | Projekt: {self.state.project_root}"
        )

    def _show(self, payload: Any) -> None:
        self.detail.configure(state="normal")
        self.detail.delete("1.0", "end")
        self.detail.insert("1.0", json.dumps(payload, indent=2, ensure_ascii=False, default=str))
        self.detail.configure(state="disabled")


def run_gui(project_root: str | Path = ".", initial_module: str = "chat") -> int:
    app = AIWorkspaceApp(project_root, initial_module=initial_module)
    app.mainloop()
    return 0
