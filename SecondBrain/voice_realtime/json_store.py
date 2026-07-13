from __future__ import annotations
from pathlib import Path
from typing import Any
import json

class JsonStore:
    def __init__(self, root: str | Path):
        self.root = Path(root); self.root.mkdir(parents=True, exist_ok=True)
    def path(self, name: str) -> Path: return self.root / f'{name}.json'
    def read(self, name: str, default: Any):
        p=self.path(name)
        if not p.exists(): return default
        try: return json.loads(p.read_text(encoding='utf-8'))
        except Exception: return default
    def write(self, name: str, data: Any):
        p=self.path(name); p.parent.mkdir(parents=True, exist_ok=True)
        tmp=p.with_suffix('.tmp')
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        tmp.replace(p)
        return data
    def append(self, name: str, item: Any, limit: int | None = None):
        arr=self.read(name, [])
        if not isinstance(arr, list): arr=[]
        arr.append(item)
        if limit: arr=arr[-limit:]
        self.write(name, arr)
        return item
