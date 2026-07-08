"""P5 v23.2 - Persistent GUI Settings."""

import json
from pathlib import Path


class PersistentGuiSettings:
    def __init__(self, path: str = "runtime/gui/settings.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, settings: dict):
        self.path.write_text(json.dumps(settings, indent=2), encoding="utf-8")

    def load(self):
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))
