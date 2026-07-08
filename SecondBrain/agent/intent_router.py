from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class IntentRoute:
    intent: str
    tool_name: str | None = None
    confidence: float = 1.0
    parameters: dict[str, object] = field(default_factory=dict)
    reason: str = ""


class IntentRouter:
    """Small deterministic router for first Jarvis foundation flows."""

    def __init__(self) -> None:
        self._rules: list[tuple[str, IntentRoute]] = []

    def add_keyword_rule(self, keyword: str, route: IntentRoute) -> None:
        normalized = keyword.strip().lower()
        if not normalized:
            raise ValueError("keyword_required")
        self._rules.append((normalized, route))

    def route(self, text: str) -> IntentRoute:
        normalized = (text or "").strip().lower()
        if not normalized:
            return IntentRoute(intent="empty", confidence=0.0, reason="empty_input")
        for keyword, route in self._rules:
            if keyword in normalized:
                return route
        return IntentRoute(intent="chat", confidence=0.25, reason="fallback_chat")
