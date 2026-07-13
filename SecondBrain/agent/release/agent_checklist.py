from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class AgentChecklistItem:
    key: str
    label: str
    passed: bool
    required: bool = True


class AgentChecklist:
    """Builds a deterministic RC1 checklist for the agent layer."""

    DEFAULT_ITEMS: tuple[tuple[str, str], ...] = (
        ("foundation", "Agent foundation implemented"),
        ("memory", "Memory and context guarded"),
        ("planning", "Planning and execution available"),
        ("tools", "Tool-calling framework validated"),
        ("background", "Background agent jobs available"),
        ("approvals", "Dangerous operations require approval"),
        ("privacy", "Privacy mode blocks memory writes"),
        ("audit", "Tool calls and plans are auditable"),
    )

    def build(self, passed_keys: Iterable[str]) -> list[AgentChecklistItem]:
        passed = set(passed_keys)
        return [
            AgentChecklistItem(key=key, label=label, passed=key in passed)
            for key, label in self.DEFAULT_ITEMS
        ]

    def complete(self, items: Iterable[AgentChecklistItem]) -> bool:
        return all(item.passed for item in items if item.required)
