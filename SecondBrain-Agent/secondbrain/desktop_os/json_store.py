
from __future__ import annotations
from pathlib import Path
from typing import Any
import json

class JsonStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def read(self, name: str, default: Any):
        path = self.root / name
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            return default

    def write(self, name: str, value: Any):
        path = self.root / name
        tmp = path.with_suffix(path.suffix + '.tmp')
        tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True), encoding='utf-8')
        tmp.replace(path)
        return value
