from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Iterable

_PATCH_RE = re.compile(r"^PATCH_(?P<key>P\d+_\d+(?:_\d+)?|P\d+_\d+|P\d+)_REPORT\.md$")
_VALIDATION_RE = re.compile(r"(?P<count>\d+)\s+passed(?:\s+in\s+(?P<seconds>[0-9.]+)s)?")


@dataclass(frozen=True)
class PatchRecord:
    key: str
    report_path: str
    title: str
    validation: str | None = None
    passed_count: int | None = None
    duration_seconds: float | None = None

    @property
    def sort_key(self) -> tuple[int, ...]:
        numbers = re.findall(r"\d+", self.key)
        return tuple(int(n) for n in numbers)


@dataclass(frozen=True)
class ReleaseManifest:
    current_version: str
    phase: str
    patches: tuple[PatchRecord, ...] = field(default_factory=tuple)
    test_count: int | None = None
    release_state: str = "UNKNOWN"

    def summary(self) -> dict[str, object]:
        return {
            "current_version": self.current_version,
            "phase": self.phase,
            "patch_count": len(self.patches),
            "test_count": self.test_count,
            "release_state": self.release_state,
            "latest_patch": self.patches[-1].key if self.patches else None,
        }

    def markdown(self) -> str:
        lines = [
            f"# SecondBrainAgent Release Manifest",
            "",
            f"- Current version: `{self.current_version}`",
            f"- Phase: `{self.phase}`",
            f"- Release state: `{self.release_state}`",
            f"- Test count: `{self.test_count if self.test_count is not None else 'unknown'}`",
            f"- Patch count: `{len(self.patches)}`",
            "",
            "## Patch history",
            "",
            "| Patch | Title | Validation |",
            "|---|---|---|",
        ]
        for patch in self.patches:
            validation = patch.validation or "not recorded"
            lines.append(f"| `{patch.key}` | {patch.title} | {validation} |")
        lines.append("")
        return "\n".join(lines)


def _read_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or fallback
    return fallback


def _read_validation(text: str) -> tuple[str | None, int | None, float | None]:
    for line in text.splitlines():
        match = _VALIDATION_RE.search(line)
        if match:
            count = int(match.group("count"))
            seconds = float(match.group("seconds")) if match.group("seconds") else None
            return match.group(0), count, seconds
    return None, None, None


def discover_patch_records(root: str | Path) -> tuple[PatchRecord, ...]:
    base = Path(root)
    records: list[PatchRecord] = []
    for path in base.glob("PATCH_*_REPORT.md"):
        match = _PATCH_RE.match(path.name)
        if not match:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        validation, passed_count, duration = _read_validation(text)
        records.append(
            PatchRecord(
                key=match.group("key"),
                report_path=str(path.relative_to(base)),
                title=_read_title(text, match.group("key")),
                validation=validation,
                passed_count=passed_count,
                duration_seconds=duration,
            )
        )
    return tuple(sorted(records, key=lambda item: item.sort_key))


def build_release_manifest(
    root: str | Path,
    *,
    current_version: str = "P1.4.1",
    phase: str = "P1 release consolidation",
    test_count: int | None = None,
    release_state: str = "CONDITIONAL_PASS",
) -> ReleaseManifest:
    patches = discover_patch_records(root)
    derived_test_count = test_count
    if derived_test_count is None:
        passed_counts = [p.passed_count for p in patches if p.passed_count is not None]
        derived_test_count = max(passed_counts) if passed_counts else None
    return ReleaseManifest(
        current_version=current_version,
        phase=phase,
        patches=patches,
        test_count=derived_test_count,
        release_state=release_state,
    )


def write_release_manifest(root: str | Path, output_path: str | Path = "RELEASE_MANIFEST.md", **kwargs) -> Path:
    base = Path(root)
    manifest = build_release_manifest(base, **kwargs)
    target = base / output_path
    target.write_text(manifest.markdown(), encoding="utf-8")
    return target
