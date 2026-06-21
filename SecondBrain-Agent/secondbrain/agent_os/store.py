import json
from pathlib import Path
from typing import Any


class JsonStore:
    def __init__(self, root: str | Path = ".", namespace: str = "agent_os"):
        self.root = Path(root)
        self.base = self.root / "data" / namespace
        self.base.mkdir(parents=True, exist_ok=True)

    def load(self, name: str, default: Any):
        path = self.base / f"{name}.json"
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, name: str, value: Any) -> None:
        path = self.base / f"{name}.json"
        path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")

    def append(self, name: str, item: dict) -> dict:
        items = self.load(name, [])
        items.append(item)
        self.save(name, items)
        return item
