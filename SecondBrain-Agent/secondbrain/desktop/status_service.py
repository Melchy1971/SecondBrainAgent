from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class StatusColor(StrEnum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


@dataclass(frozen=True, slots=True)
class ServiceStatus:
    name: str
    color: StatusColor
    message: str = ""


class StatusService:
    def __init__(self) -> None:
        self._statuses: dict[str, ServiceStatus] = {}

    def set_status(self, name: str, color: StatusColor, message: str = "") -> ServiceStatus:
        status = ServiceStatus(name=name, color=color, message=message)
        self._statuses[name] = status
        return status

    def get_status(self, name: str) -> ServiceStatus | None:
        return self._statuses.get(name)

    def snapshot(self) -> dict[str, ServiceStatus]:
        return dict(self._statuses)

    def overall(self) -> StatusColor:
        colors = {status.color for status in self._statuses.values()}
        if StatusColor.RED in colors:
            return StatusColor.RED
        if StatusColor.YELLOW in colors:
            return StatusColor.YELLOW
        return StatusColor.GREEN
