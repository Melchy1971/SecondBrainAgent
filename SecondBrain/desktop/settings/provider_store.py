from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .provider_profiles import ProviderKind, ProviderProfile


class ProviderProfileStore:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def load(self) -> list[ProviderProfile]:
        if not self.path.exists():
            return []
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        profiles: list[ProviderProfile] = []
        for item in raw.get("profiles", []):
            profiles.append(ProviderProfile(
                profile_id=item["profile_id"],
                kind=ProviderKind(item["kind"]),
                provider=item["provider"],
                enabled=bool(item.get("enabled", True)),
                values=dict(item.get("values", {})),
            ))
        return profiles

    def save(self, profiles: list[ProviderProfile]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {
            "profiles": [
                {
                    "profile_id": profile.profile_id,
                    "kind": profile.kind.value,
                    "provider": profile.provider,
                    "enabled": profile.enabled,
                    "values": profile.values,
                }
                for profile in profiles
            ]
        }
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
