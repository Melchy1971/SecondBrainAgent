"""P4 v22.2 - Persistent OAuth Token Repository."""

import json
from pathlib import Path


class TokenRepository:
    def __init__(self, path: str = "runtime/connectors/tokens.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, provider: str, token: dict):
        data = self.load_all()
        data[provider] = token
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load_all(self):
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))
