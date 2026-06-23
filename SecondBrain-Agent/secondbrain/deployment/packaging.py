from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
import fnmatch
import hashlib
import json
from typing import Iterable

DEFAULT_INCLUDE_SUFFIXES = (
    ".py",
    ".md",
    ".txt",
    ".ini",
    ".toml",
    ".json",
    ".yaml",
    ".yml",
)
DEFAULT_EXCLUDE_PATTERNS = (
    ".git/*",
    "*/.git/*",
    "__pycache__/*",
    "*/__pycache__/*",
    ".pytest_cache/*",
    "*/.pytest_cache/*",
    "*.pyc",
    "*.pyo",
    "*.sqlite",
    "*.sqlite3",
    "*.db",
    "*.log",
    "*.zip",
)


@dataclass(frozen=True)
class PackagingRules:
    include_suffixes: tuple[str, ...] = DEFAULT_INCLUDE_SUFFIXES
    exclude_patterns: tuple[str, ...] = DEFAULT_EXCLUDE_PATTERNS
    required_files: tuple[str, ...] = ("README.md",)
    required_dirs: tuple[str, ...] = ("secondbrain", "tests")

    def allows(self, relative_path: str, *, is_file: bool) -> bool:
        normalized = relative_path.replace("\\", "/")
        if any(fnmatch.fnmatch(normalized, pattern) for pattern in self.exclude_patterns):
            return False
        if not is_file:
            return True
        return Path(normalized).suffix in self.include_suffixes


@dataclass(frozen=True)
class PackageFile:
    path: str
    size_bytes: int
    sha256: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PackageManifest:
    version: str
    files: tuple[PackageFile, ...] = field(default_factory=tuple)
    excluded_count: int = 0
    status: str = "UNKNOWN"
    issues: tuple[str, ...] = field(default_factory=tuple)

    @property
    def file_count(self) -> int:
        return len(self.files)

    @property
    def total_size_bytes(self) -> int:
        return sum(item.size_bytes for item in self.files)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["file_count"] = self.file_count
        payload["total_size_bytes"] = self.total_size_bytes
        return payload


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def collect_package_files(root: str | Path, *, rules: PackagingRules | None = None) -> tuple[tuple[PackageFile, ...], int]:
    base = Path(root)
    if not base.exists():
        raise FileNotFoundError(str(base))
    active_rules = rules or PackagingRules()
    files: list[PackageFile] = []
    excluded = 0
    for path in sorted(base.rglob("*")):
        rel = path.relative_to(base).as_posix()
        if path.is_dir():
            if not active_rules.allows(rel + "/", is_file=False):
                excluded += 1
            continue
        if not active_rules.allows(rel, is_file=True):
            excluded += 1
            continue
        files.append(PackageFile(path=rel, size_bytes=path.stat().st_size, sha256=_hash_file(path)))
    return tuple(files), excluded


def validate_package_manifest(root: str | Path, manifest: PackageManifest, *, rules: PackagingRules | None = None) -> tuple[str, tuple[str, ...]]:
    base = Path(root)
    active_rules = rules or PackagingRules()
    issues: list[str] = []
    indexed = {item.path for item in manifest.files}

    for required in active_rules.required_files:
        if not (base / required).is_file():
            issues.append(f"missing required file: {required}")
        elif required not in indexed:
            issues.append(f"required file excluded from package: {required}")

    for required in active_rules.required_dirs:
        if not (base / required).is_dir():
            issues.append(f"missing required directory: {required}")

    if not manifest.files:
        issues.append("package contains no files")

    duplicate_paths = len(indexed) != len(manifest.files)
    if duplicate_paths:
        issues.append("package manifest contains duplicate paths")

    return ("PASS" if not issues else "FAIL", tuple(issues))


def build_package_manifest(root: str | Path, *, version: str, rules: PackagingRules | None = None) -> PackageManifest:
    files, excluded = collect_package_files(root, rules=rules)
    draft = PackageManifest(version=version, files=files, excluded_count=excluded, status="PENDING")
    status, issues = validate_package_manifest(root, draft, rules=rules)
    return PackageManifest(version=version, files=files, excluded_count=excluded, status=status, issues=issues)


def write_package_manifest(root: str | Path, *, version: str, output_path: str | Path | None = None, rules: PackagingRules | None = None) -> PackageManifest:
    base = Path(root)
    manifest = build_package_manifest(base, version=version, rules=rules)
    target = Path(output_path) if output_path is not None else base / "release" / "package_manifest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return manifest
