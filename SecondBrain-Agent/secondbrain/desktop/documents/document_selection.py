"""Selection state for document center."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DocumentSelection:
    selected_ids: set[str] = field(default_factory=set)

    def select(self, document_id: str) -> None:
        self.selected_ids.add(document_id)

    def deselect(self, document_id: str) -> None:
        self.selected_ids.discard(document_id)

    def toggle(self, document_id: str) -> None:
        if document_id in self.selected_ids:
            self.deselect(document_id)
        else:
            self.select(document_id)

    def clear(self) -> None:
        self.selected_ids.clear()

    def replace(self, document_ids: list[str] | set[str] | tuple[str, ...]) -> None:
        self.selected_ids = set(document_ids)

    def to_list(self) -> list[str]:
        return sorted(self.selected_ids)
