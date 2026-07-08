"""Voice command routing + agent integration.

Pure routing (regex intents) is unit-testable; the agent handler is an injected
callback that dispatches to the existing agent layer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class Intent:
    name: str
    slots: dict[str, str] = field(default_factory=dict)
    matched: bool = True


Handler = Callable[[Intent], Any]


class VoiceCommandRouter:
    def __init__(self, *, agent: Callable[[str], Any] | None = None) -> None:
        self._intents: list[tuple[str, re.Pattern, Handler | None]] = []
        self.agent = agent

    def register(self, name: str, pattern: str, handler: Handler | None = None) -> "VoiceCommandRouter":
        self._intents.append((name, re.compile(pattern, re.I), handler))
        return self

    def route(self, text: str) -> Intent:
        for name, pattern, _ in self._intents:
            m = pattern.search(text)
            if m:
                return Intent(name=name, slots={k: v for k, v in m.groupdict().items() if v is not None})
        return Intent(name="fallback", slots={}, matched=False)

    def handle(self, text: str) -> dict[str, Any]:
        intent = self.route(text)
        result: Any = None
        handled = False
        if intent.matched:
            handler = next((h for n, _, h in self._intents if n == intent.name), None)
            if handler is not None:
                result = handler(intent)
                handled = True
        if not handled and self.agent is not None:
            result = self.agent(text)
            handled = True
        return {"intent": intent.name, "slots": intent.slots, "matched": intent.matched,
                "handled": handled, "result": result}
