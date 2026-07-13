from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class SettingsVersion:
    major: int
    minor: int = 0
    patch: int = 0

    @classmethod
    def parse(cls, value: str) -> "SettingsVersion":
        parts = [int(part) for part in str(value).split(".") if part != ""]
        if not parts:
            raise ValueError("version must not be empty")
        padded = (parts + [0, 0])[:3]
        return cls(padded[0], padded[1], padded[2])

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


def is_compatible(current: str, target: str) -> bool:
    current_version = SettingsVersion.parse(current)
    target_version = SettingsVersion.parse(target)
    return current_version.major == target_version.major and current_version >= target_version
