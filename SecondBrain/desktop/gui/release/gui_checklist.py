from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChecklistItem:
    key: str
    label: str
    required: bool = True


class GuiRc1Checklist:
    def items(self) -> list[ChecklistItem]:
        return [
            ChecklistItem("desktop_foundation", "Desktop foundation is available"),
            ChecklistItem("dashboard", "Dashboard RC1 is available"),
            ChecklistItem("documents", "Document center RC1 is available"),
            ChecklistItem("search", "Search RC1 is available"),
            ChecklistItem("connectors", "Connector center RC1 is available"),
            ChecklistItem("settings", "Settings RC1 is available"),
            ChecklistItem("e2e_flows", "End-to-end desktop flows are validated"),
            ChecklistItem("accessibility", "Accessibility and error states are validated"),
            ChecklistItem("tests", "Automated tests pass"),
        ]

    def missing_required(self, completed: set[str]) -> list[ChecklistItem]:
        return [item for item in self.items() if item.required and item.key not in completed]
