from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
import json
import re

from .build_info import BuildInfo, create_build_info

_PATCH_RE = re.compile(r"^PATCH_(?P<key>P\d+(?:_\d+)*)_REPORT\.md$")
_PASSED_RE = re.compile(r"(?P<count>\d+)\s+passed(?:\s+in\s+(?P<seconds>[0-9.]+)s)?")
_COLLECTED_RE = re.compile(r"(?P<count>\d+)\s+tests collected")


@dataclass(frozen=True)
class PatchEntry:
    key: str
    title: str
    path: str
    passed: int | None = None
    collected: int | None = None
    duration_seconds: float | None = None

    def order(self) -> tuple[int, ...]:
        return tuple(int(v) for v in re.findall(r"\d+", self.key))


@dataclass(frozen=True)
class ReleaseManifestV2:
    version: str
    build: BuildInfo
    patches: tuple[PatchEntry, ...] = field(default_factory=tuple)
    status: str = "UNKNOWN"

    @property
    def highest_passed(self) -> int | None:
        values = [p.passed for p in self.patches if p.passed is not None]
        return max(values) if values else None

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["highest_passed"] = self.highest_passed
        data["patch_count"] = len(self.patches)
        return data


def _first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or fallback
    return fallback


def _numbers(text: str) -> tuple[int | None, int | None, float | None]:
    passed_match = _PASSED_RE.search(text)
    collected_match = _COLLECTED_RE.search(text)
    passed = int(passed_match.group("count")) if passed_match else None
    duration = float(passed_match.group("seconds")) if passed_match and passed_match.group("seconds") else None
    collected = int(collected_match.group("count")) if collected_match else None
    return passed, collected, duration


def discover_patch_entries(root: str | Path) -> tuple[PatchEntry, ...]:
    base = Path(root)
    entries: list[PatchEntry] = []
    for path in base.glob("PATCH_*_REPORT.md"):
        match = _PATCH_RE.match(path.name)
        if not match:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        passed, collected, duration = _numbers(text)
        entries.append(PatchEntry(
            key=match.group("key"),
            title=_first_heading(text, match.group("key")),
            path=str(path.relative_to(base)),
            passed=passed,
            collected=collected,
            duration_seconds=duration,
        ))
    return tuple(sorted(entries, key=lambda p: p.order()))


def generate_manifest(root: str | Path, *, version: str, status: str = "CONDITIONAL_PASS") -> ReleaseManifestV2:
    base = Path(root)
    return ReleaseManifestV2(
        version=version,
        build=create_build_info(base, version=version),
        patches=discover_patch_entries(base),
        status=status,
    )


def write_manifest(root: str | Path, *, version: str, output_path: str | Path = "release/manifest.json", status: str = "CONDITIONAL_PASS") -> Path:
    base = Path(root)
    manifest = generate_manifest(base, version=version, status=status)
    target = base / output_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return target
