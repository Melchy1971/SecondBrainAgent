from __future__ import annotations

import json
from pathlib import Path

from .connector_models import ConnectorConfig


class ConnectorConfigStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load_all(self) -> dict[str, ConnectorConfig]:
        if not self.path.exists():
            return {}
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return {
            connector_id: ConnectorConfig(
                connector_id=connector_id,
                enabled=bool(payload.get("enabled", False)),
                settings=dict(payload.get("settings", {})),
                secrets_ref=payload.get("secrets_ref"),
            )
            for connector_id, payload in raw.items()
        }

    def save_all(self, configs: dict[str, ConnectorConfig]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {connector_id: config.sanitized() | {"secrets_ref": config.secrets_ref} for connector_id, config in configs.items()}
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
