from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
import json
import re

_VERSION_PATTERNS = (
    re.compile(r"version\s*[:=]\s*[`\"]?(?P<version>P?\d+(?:\.\d+){1,2}(?:[-_][A-Za-z0-9._-]+)?)", re.IGNORECASE),
    re.compile(r"Current version:\s*`(?P<version>[^`]+)`", re.IGNORECASE),
)


@dataclass(frozen=True)
class ConsistencyIssue:
    code: str
    severity: str
    message: str
    path: str | None = None


@dataclass(frozen=True)
class ConsistencyReport:
    expected_version: str
    status: str
    discovered_versions: dict[str, str] = field(default_factory=dict)
    issues: tuple[ConsistencyIssue, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @property
    def ok(self) -> bool:
        return self.status == "PASS"


def _read_version_from_text(text: str) -> str | None:
    for pattern in _VERSION_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group("version").strip()
    return None


def _read_version_from_json(path: Path) -> str | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if isinstance(data, dict):
        value = data.get("version") or data.get("current_version")
        if isinstance(value, str):
            return value
        build = data.get("build")
        if isinstance(build, dict) and isinstance(build.get("version"), str):
            return build["version"]
    return None


def collect_versions(root: str | Path, *, candidate_files: tuple[str, ...] = ("README.md", "RELEASE_MANIFEST.md", "release/manifest.json", "release/build.json")) -> dict[str, str]:
    base = Path(root)
    versions: dict[str, str] = {}
    for rel in candidate_files:
        path = base / rel
        if not path.exists() or not path.is_file():
            continue
        version = _read_version_from_json(path) if path.suffix == ".json" else _read_version_from_text(path.read_text(encoding="utf-8", errors="replace"))
        if version:
            versions[rel] = version
    return versions


def validate_release_consistency(root: str | Path, *, expected_version: str) -> ConsistencyReport:
    base = Path(root)
    issues: list[ConsistencyIssue] = []
    if not base.exists():
        return ConsistencyReport(expected_version, "FAIL", {}, (ConsistencyIssue("ROOT_MISSING", "ERROR", f"root does not exist: {base}"),))

    versions = collect_versions(base)
    if not versions:
        issues.append(ConsistencyIssue("NO_VERSION_SOURCE", "ERROR", "no release version source found"))

    for path, version in versions.items():
        if version != expected_version:
            issues.append(ConsistencyIssue("VERSION_MISMATCH", "ERROR", f"expected {expected_version}, found {version}", path))

    for required in ("README.md", "release/manifest.json", "release/build.json"):
        if not (base / required).exists():
            issues.append(ConsistencyIssue("MISSING_RELEASE_FILE", "WARNING", f"missing {required}", required))

    status = "FAIL" if any(i.severity == "ERROR" for i in issues) else ("CONDITIONAL_PASS" if issues else "PASS")
    return ConsistencyReport(expected_version=expected_version, status=status, discovered_versions=versions, issues=tuple(issues))


def write_consistency_report(root: str | Path, *, expected_version: str, output_path: str | Path = "release/validation.json") -> Path:
    base = Path(root)
    report = validate_release_consistency(base, expected_version=expected_version)
    target = base / output_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return target
