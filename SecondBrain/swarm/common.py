
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json, time, uuid, hashlib

def now_ts() -> float:
    return time.time()

def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

def stable_id(prefix: str, value: str) -> str:
    return f"{prefix}_{hashlib.sha256(value.encode('utf-8')).hexdigest()[:12]}"

class JsonStore:
    def __init__(self, path: str | Path, default: Any):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.default = default
        if not self.path.exists():
            self.write(default)

    def read(self) -> Any:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return self.default.copy() if isinstance(self.default, dict) else list(self.default)

    def write(self, data: Any) -> None:
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def append(self, row: dict[str, Any]) -> dict[str, Any]:
        data = self.read()
        if not isinstance(data, list):
            data = []
        data.append(row)
        self.write(data)
        return row
