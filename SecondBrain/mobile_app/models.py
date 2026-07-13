from dataclasses import dataclass, asdict
from typing import Any, Dict


@dataclass
class MobileDevice:
    id: str
    name: str
    platform: str
    trusted: bool = False
    biometric_enabled: bool = False
    last_seen: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MobileCommand:
    id: str
    device_id: str
    command: str
    payload: Dict[str, Any]
    status: str = "queued"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MobileWidget:
    id: str
    name: str
    kind: str
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
