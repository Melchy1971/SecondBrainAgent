"""Search RC1 checklist."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SearchChecklistItem:
    key: str
    label: str
    done: bool
    required: bool = True


@dataclass(frozen=True)
class SearchChecklist:
    items: tuple[SearchChecklistItem, ...]

    @property
    def complete(self) -> bool:
        return all(item.done for item in self.items if item.required)

    def missing_required(self) -> tuple[str, ...]:
        return tuple(item.key for item in self.items if item.required and not item.done)

    def to_dict(self) -> dict[str, object]:
        return {
            "complete": self.complete,
            "missing_required": list(self.missing_required()),
            "items": [item.__dict__ for item in self.items],
        }


def build_default_search_checklist(flags: dict[str, bool]) -> SearchChecklist:
    labels = {
        "foundation": "Search Foundation",
        "hybrid_search_ui": "Hybrid Search UI",
        "preview_highlighting": "Preview and Highlighting",
        "saved_searches": "Saved Searches",
        "persistence": "Persistence",
        "tests": "Tests",
        "no_critical_blockers": "No Critical Blockers",
    }
    return SearchChecklist(tuple(SearchChecklistItem(k, v, bool(flags.get(k, False))) for k, v in labels.items()))
