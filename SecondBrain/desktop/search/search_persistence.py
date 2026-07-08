from __future__ import annotations

import json
from pathlib import Path
from .search_history import SearchHistory


class SearchPersistence:
    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.history_path = self.base_dir / "history.json"
        self.preferences_path = self.base_dir / "preferences.json"

    def save_history(self, history: SearchHistory) -> None:
        self.history_path.write_text(json.dumps(history.entries, indent=2), encoding="utf-8")

    def load_history(self) -> SearchHistory:
        if not self.history_path.exists():
            return SearchHistory()
        entries = json.loads(self.history_path.read_text(encoding="utf-8"))
        return SearchHistory(entries=list(entries))
