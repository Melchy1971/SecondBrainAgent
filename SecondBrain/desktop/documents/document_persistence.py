"""JSON persistence for document center view state."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class DocumentPersistence:
    def __init__(self, base_path: str | Path) -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_json(self, name: str, data: dict[str, Any]) -> Path:
        path = self.base_path / name
        path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def load_json(self, name: str, default: dict[str, Any] | None = None) -> dict[str, Any]:
        path = self.base_path / name
        if not path.exists():
            return dict(default or {})
        return json.loads(path.read_text(encoding="utf-8"))

    def save_selection(self, selected_ids: list[str]) -> Path:
        return self.save_json("selection.json", {"selected_ids": selected_ids})

    def load_selection(self) -> list[str]:
        return list(self.load_json("selection.json", {"selected_ids": []}).get("selected_ids", []))
