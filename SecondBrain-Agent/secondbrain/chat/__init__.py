"""v30.46.1 - AI Chat Foundation: gemeinsame Chat-Architektur.

Buendelt die bestehenden Chat-Bausteine hinter einer Fassade mit einer API:

    from secondbrain.chat import ChatService

    chat = ChatService(project_root)
    chat.ask("Frage")
    chat.stream("Frage", on_chunk=..., on_done=...)
    chat.retry()
    chat.cancel()
    chat.export(conversation_id, format="md")
    chat.import_(pfad)          # "import" ist Python-Schluesselwort

Bausteine (kein Neubau, konsolidiert aus Bestand):
- ChatService            Fassade (secondbrain.chat.service)
- ConversationStore      Persistenz (re-export aus secondbrain.native.chat)
- ConversationState      UI-unabhaengiger Konversationszustand
- StreamingManager       non-blocking Streaming (vormals gui.chat_stream.ChatStream)
- MarkdownRenderer       Markdown-Parser/Tk-Renderer (vormals secondbrain.markdown)
- CitationRenderer       Zitat-Normalisierung fuer GUI/HUD/CLI
- ConversationExporter   Export json/md (delegiert an ConversationStore)
- ConversationImporter   Re-Import exportierter Konversationen

Die Importe sind lazy (PEP 562), damit leichte Konsumenten (z. B.
secondbrain.markdown) keine Provider-Abhaengigkeiten ziehen.
"""
from __future__ import annotations

import importlib
from typing import Any

_EXPORTS = {
    "ChatService": "secondbrain.chat.service",
    "ConversationState": "secondbrain.chat.state",
    "StreamingManager": "secondbrain.chat.streaming",
    "MarkdownRenderer": "secondbrain.chat.markdown_renderer",
    "CitationRenderer": "secondbrain.chat.citations",
    "ConversationExporter": "secondbrain.chat.io",
    "ConversationImporter": "secondbrain.chat.io",
    "Conversation": "secondbrain.native.chat",
    "ConversationStore": "secondbrain.native.chat",
}

__all__ = sorted(_EXPORTS)


def __getattr__(name: str) -> Any:
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module 'secondbrain.chat' has no attribute {name!r}")
    return getattr(importlib.import_module(module_name), name)


def __dir__() -> list[str]:
    return __all__
