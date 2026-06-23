from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DesktopRCChecklistState(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


@dataclass(frozen=True)
class DesktopRCChecklistItem:
    key: str
    title: str
    state: DesktopRCChecklistState
    evidence: str = ""
    blocking: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "title": self.title,
            "state": self.state.value,
            "evidence": self.evidence,
            "blocking": self.blocking,
        }


@dataclass
class DesktopRCChecklist:
    items: list[DesktopRCChecklistItem] = field(default_factory=list)

    def add(
        self,
        key: str,
        title: str,
        state: DesktopRCChecklistState | str,
        evidence: str = "",
        blocking: bool = False,
    ) -> None:
        self.items.append(
            DesktopRCChecklistItem(
                key=key,
                title=title,
                state=DesktopRCChecklistState(state),
                evidence=evidence,
                blocking=blocking,
            )
        )

    @property
    def blocking_failures(self) -> list[DesktopRCChecklistItem]:
        return [item for item in self.items if item.blocking and item.state == DesktopRCChecklistState.FAIL]

    @property
    def warnings(self) -> list[DesktopRCChecklistItem]:
        return [item for item in self.items if item.state == DesktopRCChecklistState.WARNING]

    @property
    def passed(self) -> bool:
        return not self.blocking_failures

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "items": [item.to_dict() for item in self.items],
            "blocking_failures": [item.key for item in self.blocking_failures],
            "warnings": [item.key for item in self.warnings],
        }
