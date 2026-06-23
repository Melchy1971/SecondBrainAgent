from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class ConnectorCenterMetrics:
    total_connectors: int = 0
    enabled_connectors: int = 0
    disabled_connectors: int = 0
    running_jobs: int = 0
    failed_jobs: int = 0
    healthy_connectors: int = 0
    degraded_connectors: int = 0
    unavailable_connectors: int = 0

    @property
    def health_ratio(self) -> float:
        if self.total_connectors <= 0:
            return 1.0
        return round(self.healthy_connectors / self.total_connectors, 4)

    @property
    def has_blocking_failures(self) -> bool:
        return self.unavailable_connectors > 0 or self.failed_jobs > 0

    def to_dict(self) -> dict[str, int | float | bool]:
        data = asdict(self)
        data["health_ratio"] = self.health_ratio
        data["has_blocking_failures"] = self.has_blocking_failures
        return data
