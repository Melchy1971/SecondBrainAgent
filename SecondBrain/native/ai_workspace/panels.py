"""v30.46.3 - UI-unabhaengige Panel-Modelle des AI Workspace.

Vier Zonen (eine Navigation, eine Toolbar — beides in AIWorkspaceApp):

    LINKS   Navigation (Dashboard, Workspace, Dokumente, Memory, Agenten, Voice)
    MITTE   Conversation / Streaming / Markdown (ChatPanel)
    RECHTS  Quellen / Memory / Dokumente / Runtime (SourcePanel, MemoryPanel,
            DocumentPanel, RuntimePanel)
    UNTEN   Prompt / Anhaenge / Sprache / Provider (PromptBar)

Die Modelle sind Tk-frei und werden von den Widgets in gui.py konsumiert;
Tests laufen ohne Display.
"""
from __future__ import annotations

from typing import Any, Iterable

from secondbrain.chat.citations import CitationRenderer

NAVIGATION_PRIMARY = ("dashboard", "workspace", "documents", "memory", "agents", "voice")

PROVIDERS = ("openai", "ollama", "gemini", "claude")

CONTEXT_SOURCES = ("documents", "folders", "ocr", "memory", "github", "mail", "csv")


class ChatPanel:
    """MITTE: Conversation-Transkript (Markdown) und aktuelle Zitate."""

    @staticmethod
    def transcript_markdown(messages: Iterable[dict[str, Any]]) -> str:
        return "\n\n".join(
            f"## {str(row.get('role', '')).title()}\n\n{row.get('content', '')}" for row in messages
        )

    @staticmethod
    def latest_citations(messages: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        latest = next(
            (row for row in reversed(list(messages)) if row.get("role") == "assistant"),
            None,
        )
        return list(((latest or {}).get("metadata") or {}).get("citations") or [])


class SourcePanel:
    """RECHTS/Quellen: Zitat-Zeilen fuer die Tabelle."""

    COLUMNS = CitationRenderer.COLUMNS

    def __init__(self) -> None:
        self._renderer = CitationRenderer()

    def rows(self, citations: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        return self._renderer.rows(citations)


class MemoryPanel:
    """RECHTS/Memory: Kontext-Eintraege aus dem letzten Pipeline-Lauf."""

    @staticmethod
    def lines(memory_context: Iterable[dict[str, Any]]) -> list[str]:
        lines: list[str] = []
        for row in memory_context or []:
            content = str(row.get("content") or "").strip()
            if content:
                lines.append(content)
        return lines


class DocumentPanel:
    """RECHTS/Dokumente: ausgewaehlte Dokumente + Anhaenge der Konversation."""

    @staticmethod
    def lines(selected_documents: Iterable[str], attachments: Iterable[dict[str, Any]]) -> list[str]:
        lines = [f"Auswahl: {item}" for item in selected_documents or []]
        for manifest in attachments or []:
            lines.append(
                f"Anhang: {manifest.get('name')} ({manifest.get('extension')}, {manifest.get('size')} Bytes)"
            )
        return lines


class RuntimePanel:
    """RECHTS/Runtime: Laufzeitzustand aus dem ApplicationState."""

    @staticmethod
    def snapshot(state: Any) -> dict[str, Any]:
        return {
            "version": getattr(state, "version", ""),
            "status": getattr(state, "status", ""),
            "message": getattr(state, "message", ""),
            "provider": getattr(state, "active_provider", ""),
            "model": getattr(state, "active_model", ""),
            "conversation": getattr(state, "current_conversation", None) or "-",
            "module": getattr(state, "active_module", ""),
            "updated": getattr(state, "last_updated", ""),
        }

    @classmethod
    def lines(cls, state: Any) -> list[str]:
        snapshot = cls.snapshot(state)
        order = ("version", "status", "message", "provider", "model", "conversation", "module", "updated")
        return [f"{key}: {snapshot[key]}" for key in order]


class PromptBar:
    """UNTEN: Prompt, Anhaenge, Sprache, Provider."""

    PROVIDERS = PROVIDERS

    @staticmethod
    def normalize_prompt(prompt: str) -> str:
        return (prompt or "").strip()

    @staticmethod
    def validate_provider(provider: str) -> str:
        candidate = (provider or "").strip().lower()
        return candidate if candidate in PROVIDERS else PROVIDERS[1]

    @staticmethod
    def voice_module_id(modules: Iterable[Any]) -> str | None:
        """Findet das bestehende Voice-Modul (keine zweite Navigation)."""
        for module in modules or []:
            identifier = str(getattr(module, "id", "")).lower()
            title = str(getattr(module, "title", "")).lower()
            if "voice" in identifier or "voice" in title or "sprach" in title:
                return getattr(module, "id", None)
        return None
