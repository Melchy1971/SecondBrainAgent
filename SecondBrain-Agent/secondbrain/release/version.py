from __future__ import annotations

from dataclasses import dataclass
import re

_VERSION_RE = re.compile(r"^(?P<prefix>[A-Z]+)?(?P<major>\d+)(?:\.(?P<minor>\d+))?(?:\.(?P<patch>\d+))?(?:[-_](?P<label>[A-Za-z0-9._-]+))?$")


@dataclass(frozen=True, order=True)
class VersionInfo:
    major: int
    minor: int = 0
    patch: int = 0
    label: str | None = None
    prefix: str = "P"

    @classmethod
    def parse(cls, value: str) -> "VersionInfo":
        raw = value.strip()
        if not raw:
            raise ValueError("version must not be empty")
        match = _VERSION_RE.match(raw)
        if not match:
            raise ValueError(f"invalid version format: {value!r}")
        return cls(
            major=int(match.group("major")),
            minor=int(match.group("minor") or 0),
            patch=int(match.group("patch") or 0),
            label=match.group("label"),
            prefix=match.group("prefix") or "P",
        )

    def normalized(self) -> str:
        base = f"{self.prefix}{self.major}.{self.minor}.{self.patch}"
        return f"{base}-{self.label}" if self.label else base


CURRENT_VERSION = VersionInfo.parse("P1.4.2")
