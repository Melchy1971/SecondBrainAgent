from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass
class SettingsMetrics:
    load_time_ms: float = 0.0
    save_time_ms: float = 0.0
    snapshot_count: int = 0
    recovery_time_ms: float = 0.0
    migration_count: int = 0
    failed_validations: int = 0
    corrupted_settings_detected: int = 0
    extra: dict[str, float | int | str] = field(default_factory=dict)

    def record_timing(self, key: str, fn: Callable[[], T]) -> T:
        start = perf_counter()
        try:
            return fn()
        finally:
            elapsed = (perf_counter() - start) * 1000
            if key == "load":
                self.load_time_ms = elapsed
            elif key == "save":
                self.save_time_ms = elapsed
            elif key == "recovery":
                self.recovery_time_ms = elapsed
            else:
                self.extra[f"{key}_time_ms"] = elapsed

    def mark_validation_failed(self, count: int = 1) -> None:
        self.failed_validations += count

    def mark_corruption_detected(self, count: int = 1) -> None:
        self.corrupted_settings_detected += count

    def to_dict(self) -> dict:
        return {
            "load_time_ms": round(self.load_time_ms, 3),
            "save_time_ms": round(self.save_time_ms, 3),
            "snapshot_count": self.snapshot_count,
            "recovery_time_ms": round(self.recovery_time_ms, 3),
            "migration_count": self.migration_count,
            "failed_validations": self.failed_validations,
            "corrupted_settings_detected": self.corrupted_settings_detected,
            "extra": dict(self.extra),
        }
