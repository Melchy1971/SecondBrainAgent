"""v30.46.1 - ChatService: eine API fuer alle Chat-Oberflaechen.

Fassade ueber die bestehenden Bausteine (NativeChatService,
ConversationStore, StreamingManager). Konsumenten: AI Workspace (Tk),
Web-HUD (/api/assistant), CLI (ai-chat/conversation-*).

    chat.ask(text, **optionen)      -> dict (Antwort + Zitate)
    chat.stream(text, ...)          -> Iterator (blocking) oder
                                       StreamingManager (mit Callbacks)
    chat.retry()                    -> letzte Frage erneut
    chat.cancel()                   -> laufendes Streaming abbrechen
    chat.export(id, format=...)     -> Export via ConversationStore
    chat.import_(pfad)              -> Re-Import eines Exports
"""
from __future__ import annotations

from pathlib import Path
from threading import Event
from typing import Any, Callable, Iterator

from secondbrain.chat.io import ConversationExporter, ConversationImporter
from secondbrain.chat.state import ConversationState
from secondbrain.chat.streaming import StreamingManager
from secondbrain.native.chat import NativeChatService


class ChatService:
    def __init__(
        self,
        project_root: str | Path | None = None,
        *,
        provider_manager: Any = None,
        rag_runtime: Any = None,
        memory_explorer: Any = None,
    ) -> None:
        self.native = NativeChatService(
            project_root,
            provider_manager=provider_manager,
            rag_runtime=rag_runtime,
            memory_explorer=memory_explorer,
        )
        self.conversations = self.native.conversations
        self.attachments = self.native.attachments
        self.exporter = ConversationExporter(self.conversations)
        self.importer = ConversationImporter(self.conversations)
        self.stream_manager = StreamingManager()
        self._last_text: str | None = None
        self._last_options: dict[str, Any] = {}

    # --- Kernpfad -----------------------------------------------------------

    def ask(self, text: str, **options: Any) -> dict[str, Any]:
        """Synchrone Antwort ueber den Provider-Pfad (send)."""
        self._remember(text, options)
        return self.native.send(text, **options)

    def ask_rag(self, text: str, *, limit: int = 5) -> dict[str, Any]:
        """RAG-Bridge ohne LLM-Pflicht (launcher p1-rag-answer)."""
        return self.native.ask(text, limit=limit)

    def stream(
        self,
        text: str,
        *,
        on_chunk: Callable[[str], None] | None = None,
        on_done: Callable[[str, bool], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
        **options: Any,
    ) -> Iterator[Any] | StreamingManager:
        """Streaming-Antwort.

        Ohne Callbacks: blockierender Iterator (CLI/Tests).
        Mit Callbacks: non-blocking via StreamingManager (GUI).
        """
        self._remember(text, options)

        def factory(cancel_event: Event) -> Iterator[Any]:
            return self.native.stream_response(text, cancel_event=cancel_event, **options)

        if on_chunk is None and on_done is None and on_error is None:
            self.stream_manager.cancel_event.clear()
            return factory(self.stream_manager.cancel_event)
        started = self.stream_manager.start(
            factory,
            on_chunk=on_chunk,
            on_done=on_done,
            on_error=on_error,
        )
        if not started:
            raise RuntimeError("stream_already_running")
        return self.stream_manager

    def retry(self, **overrides: Any) -> dict[str, Any]:
        """Letzte Frage erneut stellen (synchron), Optionen ueberschreibbar."""
        if not self._last_text:
            conversation_id = overrides.pop("conversation_id", None) or self.last_conversation_id
            if conversation_id:
                return self.native.retry(conversation_id, **overrides)
            return {"ok": False, "status": "nothing_to_retry"}
        options = {**self._last_options, **overrides}
        options.setdefault("conversation_id", self.last_conversation_id)
        return self.ask(self._last_text, **options)

    def cancel(self) -> bool:
        """Laufendes Streaming abbrechen (Manager- und Iterator-Modus)."""
        if self.stream_manager.running:
            return self.stream_manager.cancel()
        self.stream_manager.cancel_event.set()
        return True

    # --- Import/Export ------------------------------------------------------

    def export(self, conversation_id: str | None = None, *, format: str = "json") -> dict[str, Any]:
        target = conversation_id or self.last_conversation_id
        if not target:
            return {"ok": False, "status": "no_conversation"}
        return self.exporter.export(target, format=format)

    def import_(self, path: str | Path) -> dict[str, Any]:
        """'import' ist Python-Schluesselwort; daher import_ mit Alias."""
        return self.importer.import_file(path)

    import_conversation = import_

    # --- Zustand ------------------------------------------------------------

    @property
    def last_conversation_id(self) -> str | None:
        return self.native.last_conversation_id

    def state(self, conversation_id: str | None = None) -> ConversationState:
        target = conversation_id or self.last_conversation_id
        if not target:
            return ConversationState()
        conversation = self.conversations.get(target)
        messages = self.conversations.messages(target) if conversation else []
        state = ConversationState.from_conversation(conversation, messages)
        if self.stream_manager.running:
            state.set_status("streaming")
        elif self.stream_manager.status == "failed":
            state.set_status("failed", error=str(self.stream_manager.error))
        return state

    # --- intern ---------------------------------------------------------------

    def _remember(self, text: str, options: dict[str, Any]) -> None:
        self._last_text = (text or "").strip() or self._last_text
        self._last_options = {key: value for key, value in options.items() if key != "cancel_event"}
