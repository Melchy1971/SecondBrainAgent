"""v30.46.3 - AI Workspace: die bestehende Desktop-GUI in vier Zonen.

LINKS   bestehende Navigation (Dashboard, Workspace, Dokumente, Memory,
        Agenten, Voice, weitere Module)
MITTE   Conversation / Streaming / Markdown
RECHTS  Quellen / Memory / Dokumente / Runtime (Notebook)
UNTEN   Prompt / Anhaenge / Sprache / Provider

Keine neue GUI, keine zweite Navigation, keine zweite Toolbar:
AIWorkspaceApp bleibt die eine Shell; die Panels konsumieren die
UI-freien Modelle aus panels.py und die gemeinsame Chat-API
(secondbrain.chat.ChatService).
"""
from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Any

from secondbrain.chat import ChatService, MarkdownRenderer
from secondbrain.native.layout_center.service import NativeLayoutService
from secondbrain.native.theme_center.service import ThemeCenterService

from .models import ApplicationState
from .panels import CONTEXT_SOURCES, ChatPanel, DocumentPanel, MemoryPanel, PromptBar, RuntimePanel, SourcePanel
from .service import AIWorkspaceService


class WorkspaceRightPanel(ttk.Frame):
    """RECHTS: Quellen, Memory, Dokumente, Runtime in einem Notebook."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=4)
        self.source_panel = SourcePanel()
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        sources = ttk.Frame(self.notebook)
        self.citations = ttk.Treeview(sources, columns=self.source_panel.COLUMNS, show="tree headings")
        self.citations.heading("#0", text="Dokument")
        for column in self.source_panel.COLUMNS:
            self.citations.heading(column, text=column.title())
            self.citations.column(column, width=70)
        self.citations.pack(fill="both", expand=True)
        self.notebook.add(sources, text="Quellen")

        self.memory_list = tk.Listbox(self.notebook)
        self.notebook.add(self.memory_list, text="Memory")

        self.document_list = tk.Listbox(self.notebook)
        self.notebook.add(self.document_list, text="Dokumente")

        self.runtime_text = tk.Text(self.notebook, wrap="word", state="disabled", width=32)
        self.notebook.add(self.runtime_text, text="Runtime")

    def update_citations(self, citations: list[dict[str, Any]]) -> None:
        for item in self.citations.get_children():
            self.citations.delete(item)
        for row in self.source_panel.rows(citations):
            self.citations.insert("", "end", iid=row["iid"], text=row["document"], values=row["values"], tags=(row["tag"],))

    def update_memory(self, memory_context: list[dict[str, Any]]) -> None:
        self.memory_list.delete(0, "end")
        for line in MemoryPanel.lines(memory_context):
            self.memory_list.insert("end", line)

    def update_documents(self, selected_documents: list[str], attachments: list[dict[str, Any]]) -> None:
        self.document_list.delete(0, "end")
        for line in DocumentPanel.lines(selected_documents, attachments):
            self.document_list.insert("end", line)

    def update_runtime(self, state: ApplicationState) -> None:
        self.runtime_text.configure(state="normal")
        self.runtime_text.delete("1.0", "end")
        self.runtime_text.insert("1.0", "\n".join(RuntimePanel.lines(state)))
        self.runtime_text.configure(state="disabled")


class WorkspaceBottomBar(ttk.Frame):
    """UNTEN: Prompt, Anhaenge, Sprache, Provider — eine Leiste fuer den Chat."""

    def __init__(self, master: tk.Misc, state: ApplicationState) -> None:
        super().__init__(master, padding=(14, 4))
        self.state = state
        self.on_start: Any = None
        self.on_cancel: Any = None
        self.on_retry: Any = None
        self.on_attach: Any = None
        self.on_voice: Any = None

        self.prompt_var = tk.StringVar()
        self.provider_var = tk.StringVar(value=state.active_provider)
        self.model_var = tk.StringVar(value=state.active_model)

        entry = ttk.Entry(self, textvariable=self.prompt_var)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda _event: self._start())
        ttk.Button(self, text="Start", command=self._start).pack(side="left", padx=3)
        ttk.Button(self, text="Cancel", command=lambda: self.on_cancel and self.on_cancel()).pack(side="left", padx=3)
        ttk.Button(self, text="Retry", command=lambda: self.on_retry and self.on_retry()).pack(side="left", padx=3)
        ttk.Button(self, text="Anhaengen", command=lambda: self.on_attach and self.on_attach()).pack(side="left", padx=(12, 3))
        self.attachment_label = ttk.Label(self, text="0 Anhaenge")
        self.attachment_label.pack(side="left", padx=3)
        ttk.Button(self, text="Sprache", command=lambda: self.on_voice and self.on_voice()).pack(side="left", padx=(12, 3))
        ttk.Label(self, text="Provider").pack(side="left", padx=(12, 2))
        ttk.Combobox(self, textvariable=self.provider_var, values=PromptBar.PROVIDERS, state="readonly", width=10).pack(side="left")
        ttk.Entry(self, textvariable=self.model_var, width=22).pack(side="left", padx=4)

    def _start(self) -> None:
        prompt = PromptBar.normalize_prompt(self.prompt_var.get())
        if not prompt or self.on_start is None:
            return
        self.prompt_var.set("")
        self.on_start(prompt)

    def set_attachment_count(self, count: int) -> None:
        self.attachment_label.configure(text=f"{count} Anhaenge")


class AIChatWorkspaceFrame(ttk.Frame):
    """MITTE: Conversation, Streaming, Markdown. Bedienung ueber die Bottom-Bar."""

    SOURCES = CONTEXT_SOURCES

    def __init__(
        self,
        master: tk.Misc,
        state: ApplicationState,
        project_root: Path,
        navigate_callback: Any = None,
        *,
        right_panel: WorkspaceRightPanel | None = None,
        bottom_bar: WorkspaceBottomBar | None = None,
    ) -> None:
        super().__init__(master)
        self.state = state
        self.project_root = project_root
        self.navigate_callback = navigate_callback
        self.service = ChatService(project_root)
        self.stream = self.service.stream_manager
        self.renderer = MarkdownRenderer()
        self.right_panel = right_panel
        self.bottom_bar = bottom_bar
        self.last_prompt = ""
        self.source_vars = {source: tk.BooleanVar(value=source in {"documents", "memory"}) for source in CONTEXT_SOURCES}

        header = ttk.Frame(self)
        header.pack(fill="x")
        ttk.Label(header, text="Conversation", font=("Segoe UI", 11, "bold")).pack(side="left")
        for source, variable in self.source_vars.items():
            ttk.Checkbutton(header, text=source.title(), variable=variable).pack(side="left", padx=2)

        self.transcript = tk.Text(self, wrap="word", state="disabled")
        self.transcript.pack(fill="both", expand=True, pady=(6, 0))

        if self.bottom_bar is not None:
            self.bottom_bar.on_start = self.start
            self.bottom_bar.on_cancel = self.cancel
            self.bottom_bar.on_retry = self.retry
            self.bottom_bar.on_attach = self.attach_file
            self.bottom_bar.on_voice = self.open_voice
        if self.right_panel is not None:
            self.right_panel.citations.bind("<Double-1>", self.open_citation)

        self.reload_conversation()

    # --- Bedienung (Bottom-Bar-Callbacks) ------------------------------------

    def selected_sources(self) -> list[str]:
        return [source for source, variable in self.source_vars.items() if variable.get()]

    def start(self, prompt: str) -> None:
        self.last_prompt = prompt
        if self.bottom_bar is not None:
            self.state.active_provider = PromptBar.validate_provider(self.bottom_bar.provider_var.get())
            self.state.active_model = self.bottom_bar.model_var.get()
        self._start_stream(prompt)

    def _start_stream(self, prompt: str) -> None:
        try:
            self.service.stream(
                prompt,
                conversation_id=self.state.current_conversation,
                provider=self.state.active_provider,
                model=self.state.active_model,
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

    def open_voice(self) -> None:
        module_id = PromptBar.voice_module_id(self.state.modules)
        if module_id and self.navigate_callback is not None:
            self.navigate_callback(module_id)

    # --- Rendering -------------------------------------------------------------

    def _render_stream(self) -> None:
        self.renderer.render_into(self.transcript, self.stream.content())

    def _stream_done(self) -> None:
        if self.service.last_conversation_id:
            self.state.current_conversation = self.service.last_conversation_id
        self.state.status = "ready"
        self.state.message = "Antwort abgeschlossen"
        self.reload_conversation()

    def reload_conversation(self) -> None:
        messages = (
            self.service.conversations.messages(self.state.current_conversation)
            if self.state.current_conversation
            else []
        )
        self.renderer.render_into(self.transcript, ChatPanel.transcript_markdown(messages))
        citations = ChatPanel.latest_citations(messages)
        attachments = (
            self.service.attachments.list(self.state.current_conversation)
            if self.state.current_conversation
            else []
        )
        if self.right_panel is not None:
            self.right_panel.update_citations(citations)
            self.right_panel.update_memory(self.state.memory_context)
            self.right_panel.update_documents(list(self.state.selected_documents), attachments)
            self.right_panel.update_runtime(self.state)
        if self.bottom_bar is not None:
            self.bottom_bar.set_attachment_count(len(attachments))

    def open_citation(self, _event: object | None = None) -> None:
        if self.right_panel is None:
            return
        selected = self.right_panel.citations.selection()
        if not selected:
            return
        tags = self.right_panel.citations.item(selected[0], "tags")
        if tags:
            self.state.selected_documents = [str(tags[0])]
            self.state.active_workspace = "documents"
            self.state.message = f"Quelle ausgewaehlt: {tags[0]}"
            if self.navigate_callback is not None:
                self.navigate_callback("documents")

    def attach_file(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("Supported", "*.pdf *.docx *.xlsx *.csv *.txt *.png *.jpg *.jpeg *.json *.md")]
        )
        if not path:
            return
        if self.state.current_conversation is None:
            conversation = self.service.conversations.create(
                "Attachments",
                provider=self.state.active_provider,
                model=self.state.active_model,
            )
            self.state.current_conversation = str(conversation["id"])
        result = self.service.attachments.attach(self.state.current_conversation, path)
        self.state.message = result.get("status", "attachment")
        if result.get("ok") and result.get("path"):
            self.state.selected_documents = [str(result["path"])]
        self.reload_conversation()

    def _show_error(self, exc: Exception) -> None:
        self.state.set_error(f"{type(exc).__name__}: {exc}")


class AIWorkspaceApp(tk.Tk):
    """Die eine Desktop-Shell: Navigation, Toolbar, vier Zonen."""

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
        self.geometry("1400x820")
        self.minsize(1080, 660)
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
        self.inbox_button = ttk.Button(
            self.toolbar,
            text="Prüfungen & Freigaben [0]",
            command=lambda: self.navigate("review_inbox"),
        )
        self.inbox_button.pack(side="left", padx=6)
        self.module_title = ttk.Label(self.toolbar, text="", font=("Segoe UI", 11, "bold"))
        self.module_title.pack(side="right")

        # UNTEN: eine Leiste (vor dem Body gepackt, damit sie unten sitzt)
        self.status_text = tk.StringVar(value="Desktop wird initialisiert")
        self.statusbar = ttk.Label(self, textvariable=self.status_text, relief="sunken", anchor="w", padding=(8, 4))
        self.statusbar.pack(fill="x", side="bottom")
        self.bottom_bar = WorkspaceBottomBar(self, self.state)
        self.bottom_bar.pack(fill="x", side="bottom")

        layout = self.layout_service.load()["layout"]
        body = tk.PanedWindow(self, orient="horizontal", bg=background, sashwidth=4)
        body.pack(fill="both", expand=True, padx=14, pady=8)
        navigation_frame = ttk.Frame(body, padding=8)
        content_frame = ttk.Frame(body, padding=8)
        right_frame = ttk.Frame(body, padding=0)
        body.add(navigation_frame, width=layout.get("left_width", 240))
        body.add(content_frame)
        body.add(right_frame, width=layout.get("right_width", 330))

        # LINKS: die eine Navigation
        self.navigation = ttk.Treeview(navigation_frame, columns=("status",), show="tree headings", selectmode="browse")
        self.navigation.heading("#0", text="Modul")
        self.navigation.heading("status", text="Status")
        self.navigation.column("#0", width=170)
        self.navigation.column("status", width=64, anchor="center")
        self.navigation.pack(fill="both", expand=True)
        self.navigation.bind("<<TreeviewSelect>>", self._on_navigation)

        # RECHTS: Quellen/Memory/Dokumente/Runtime
        self.right_panel = WorkspaceRightPanel(right_frame)
        self.right_panel.pack(fill="both", expand=True)

        # MITTE: Detail-JSON fuer Module, Chat-Frame fuer den Chat
        self.content_frame = content_frame
        self.detail = tk.Text(content_frame, wrap="word", borderwidth=0)
        self.detail.pack(fill="both", expand=True)
        self.chat_workspace = AIChatWorkspaceFrame(
            content_frame,
            self.state,
            self.project_root,
            self.navigate,
            right_panel=self.right_panel,
            bottom_bar=self.bottom_bar,
        )
        # v30.47: Document Preview Center als eingebettete MITTE-Zone (lazy).
        self.preview_workspace: Any = None
        # v30.48: Bedienung des bestehenden ProjectCenter, keine zweite Shell.
        self.project_workspace: Any = None
        # v30.49: bestehende Agent-Tasks, Queue und Freigaben in derselben Shell.
        self.task_workspace: Any = None
        # Unified Review/Approval Inbox in derselben Shell (kein zweites Tk-Root).
        self.review_inbox_workspace: Any = None
        # v30.50: read-only Projektion der bestehenden RAG-/Memory-Daten.
        self.semantic_workspace: Any = None
        # v30.51: zentrale resumierbare Streaming-Import-Pipeline.
        self.import_workspace: Any = None
        # v30.78: editierbare Einstellungen ueber die zentrale RuntimeConfig.
        self.settings_workspace: Any = None
        # v30.78: Audit Viewer (Observability).
        self.observability_workspace: Any = None
        # v30.78: Import-Historie der einheitlichen Pipeline.
        self.import_history_workspace: Any = None
        # v30.78: Tag Editor (Review Queue, manuelle Korrekturen).
        self.tag_editor_workspace: Any = None

    def _preview_frame(self) -> Any:
        if self.preview_workspace is None:
            from secondbrain.native.document_preview.gui import DocumentPreviewFrame

            self.preview_workspace = DocumentPreviewFrame(
                self.content_frame, self.project_root, state_sink=self.state
            )
        return self.preview_workspace

    def _project_frame(self) -> Any:
        if self.project_workspace is None:
            from secondbrain.native.project_workspace_panel import ProjectWorkspaceFrame

            self.project_workspace = ProjectWorkspaceFrame(self.content_frame, self.project_root)
        return self.project_workspace

    def _task_frame(self) -> Any:
        if self.task_workspace is None:
            from secondbrain.native.task_workspace_panel import TaskWorkspaceFrame

            self.task_workspace = TaskWorkspaceFrame(self.content_frame, self.project_root)
        return self.task_workspace

    def _review_inbox_frame(self) -> Any:
        if self.review_inbox_workspace is None:
            from secondbrain.gui.approval_inbox import ApprovalInboxFrame

            self.review_inbox_workspace = ApprovalInboxFrame(
                self.content_frame,
                self.project_root,
                navigate_callback=self.navigate,
                changed_callback=self.refresh,
            )
        return self.review_inbox_workspace

    def _semantic_frame(self) -> Any:
        if self.semantic_workspace is None:
            from secondbrain.native.semantic_explorer_panel import SemanticExplorerFrame

            self.semantic_workspace = SemanticExplorerFrame(self.content_frame, self.project_root)
        return self.semantic_workspace

    def _import_frame(self) -> Any:
        if self.import_workspace is None:
            from secondbrain.native.streaming_import_panel import StreamingImportFrame

            self.import_workspace = StreamingImportFrame(self.content_frame, self.project_root)
        return self.import_workspace

    def _settings_frame(self) -> Any:
        if self.settings_workspace is None:
            from secondbrain.native.settings_workspace_panel import SettingsWorkspaceFrame

            self.settings_workspace = SettingsWorkspaceFrame(self.content_frame, self.project_root)
        return self.settings_workspace

    def _observability_frame(self) -> Any:
        if self.observability_workspace is None:
            from secondbrain.native.observability_panel import ObservabilityWorkspaceFrame

            self.observability_workspace = ObservabilityWorkspaceFrame(self.content_frame, self.project_root)
        return self.observability_workspace

    def _import_history_frame(self) -> Any:
        if self.import_history_workspace is None:
            from secondbrain.native.import_history_panel import ImportHistoryWorkspaceFrame

            self.import_history_workspace = ImportHistoryWorkspaceFrame(self.content_frame, self.project_root)
        return self.import_history_workspace

    def _tag_editor_frame(self) -> Any:
        if self.tag_editor_workspace is None:
            from secondbrain.native.tag_editor_panel import TagEditorWorkspaceFrame

            self.tag_editor_workspace = TagEditorWorkspaceFrame(self.content_frame, self.project_root)
        return self.tag_editor_workspace

    def refresh(self) -> None:
        snapshot = self.service.snapshot()
        inbox = self.service.module_payload("review_inbox")
        pending_count = int(inbox.get("pending_count", 0)) if inbox.get("ok") else 0
        critical_count = int(inbox.get("critical_count", 0)) if inbox.get("ok") else 0
        critical_marker = " !" if critical_count else ""
        self.inbox_button.configure(text=f"Prüfungen & Freigaben [{pending_count}]{critical_marker}")
        self.state.version = snapshot.version
        self.state.replace_modules(snapshot.modules)
        self.version_label.configure(text=self.state.version)
        current_selection = self.state.active_module
        for item in self.navigation.get_children():
            self.navigation.delete(item)
        for module in self.state.modules:
            title = module.title
            if module.id == "review_inbox":
                title = f"{module.title} [{pending_count}]{critical_marker}"
            self.navigation.insert("", "end", iid=module.id, text=title, values=(module.status,))
        if current_selection and self.navigation.exists(current_selection):
            self.navigation.selection_set(current_selection)
            self.navigation.focus(current_selection)
        if self.review_inbox_workspace is not None:
            self.review_inbox_workspace.reload()
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

    WORKSPACE_MODULES = {
        "chat": (None, "reload_conversation", "AI Chat Workspace bereit"),
        "preview": ("_preview_frame", "reload_documents", "Document Preview Center bereit"),
        "projects": ("_project_frame", "reload", "Projekte und Workspaces bereit"),
        "tasks": ("_task_frame", "reload", "Aufgaben, Agent Jobs und Genehmigungen bereit"),
        "semantic": ("_semantic_frame", "reload", "Semantic Explorer bereit"),
        "imports": ("_import_frame", "reload", "Enterprise Streaming Import bereit"),
        "settings": ("_settings_frame", "reload", "Einstellungen bereit (zentrale RuntimeConfig)"),
        "observability": ("_observability_frame", "reload", "Audit Viewer bereit"),
        "import_history": ("_import_history_frame", "reload", "Import-Historie bereit"),
        "tags": ("_tag_editor_frame", "reload", "Tag Editor bereit"),
    }

    def _hide_content(self) -> None:
        self.detail.pack_forget()
        self.chat_workspace.pack_forget()
        for frame in (
            self.preview_workspace,
            self.project_workspace,
            self.task_workspace,
            self.semantic_workspace,
            self.import_workspace,
            self.settings_workspace,
            self.observability_workspace,
            self.import_history_workspace,
            self.tag_editor_workspace,
        ):
            if frame is not None:
                frame.pack_forget()

    def _render_active_module(self) -> None:
        module = next((item for item in self.state.modules if item.id == self.state.active_module), None)
        if module is None:
            self._show({"ok": False, "status": "no_active_module"})
            self._update_status()
            return
        spec = self.WORKSPACE_MODULES.get(module.id)
        if spec is not None:
            getter, reload_name, message = spec
            self._hide_content()
            frame = self.chat_workspace if getter is None else getattr(self, getter)()
            frame.pack(fill="both", expand=True)
            getattr(frame, reload_name)()
            self.state.status = "ready"
            self.state.message = message
            self.module_title.configure(text=module.title)
            self._update_status()
            return
        self._hide_content()
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
        self.right_panel.update_runtime(self.state)
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
