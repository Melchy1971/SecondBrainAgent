from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ConnectorActionStatus(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    FAILED = "failed"


@dataclass(frozen=True)
class ConnectorActionResult:
    action: str
    connector_id: str
    status: ConnectorActionStatus
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ConnectorActionService:
    def sync(self, connector_id: str, enabled: bool) -> ConnectorActionResult:
        if not enabled:
            return ConnectorActionResult(
                action="sync",
                connector_id=connector_id,
                status=ConnectorActionStatus.REJECTED,
                message="connector is disabled",
            )
        return ConnectorActionResult(
            action="sync",
            connector_id=connector_id,
            status=ConnectorActionStatus.ACCEPTED,
            message="sync requested",
        )
