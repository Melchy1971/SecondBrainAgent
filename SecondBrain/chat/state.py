"""v30.46.1 - ConversationState: UI-unabhaengiger Konversationszustand.

Schlanker Zustand fuer eine einzelne Konversation. Der applikationsweite
Zustand bleibt secondbrain.native.ai_workspace.models.ApplicationState;
ConversationState ist dessen konversationsbezogenes Gegenstueck fuer
Fassade, HUD und CLI.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

VALID_STATUS = ("idle", "streaming", "completed", "cancelled", "failed")


@dataclass
class ConversationState:
    conversation_id: str | None = None
    title: str = ""
    workspace: str = "chat"
    provider: str = ""
    model: str = ""
    status: str = "idle"
    message_count: int = 0
    updated: str = ""
    pinned: bool = False
    archived: bool = False
    error: str | None = None
    citations: list[dict[str, Any]] = field(default_factory=list)

    def set_status(self, status: str, *, error: str | None = None) -> None:
        if status not in VALID_STATUS:
            raise ValueError(f"invalid conversation status: {status}")
        self.status = status
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_conversation(
        cls,
        conversation: dict[str, Any] | None,
        messages: list[dict[str, Any]] | None = None,
    ) -> "ConversationState":
        if not conversation:
            return cls()
        rows = messages or []
        latest = next((row for row in reversed(rows) if row.get("role") == "assistant"), None)
        citations = list(((latest or {}).get("metadata") or {}).get("citations") or [])
        return cls(
            conversation_id=str(conversation.get("id") or "") or None,
            title=str(conversation.get("title") or ""),
            workspace=str(conversation.get("workspace") or "chat"),
            provider=str(conversation.get("provider") or ""),
            model=str(conversation.get("model") or ""),
            status="idle",
            message_count=len(rows),
            updated=str(conversation.get("updated") or ""),
            pinned=bool(conversation.get("pinned")),
            archived=bool(conversation.get("archived")),
            citations=citations,
        )
