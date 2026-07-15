"""Deterministic and security-conscious Windows release artifact helpers."""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Iterable, Sequence

FORBIDDEN_NAMES = {".env", "auto.key", "auto.crt", "credentials.json", "secrets.json"}
FORBIDDEN_PARTS = {"tests", "test", "__pycache__", ".pytest_cache", "runtime", "data", "logs", "backups"}
SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"(?i)(?:api[_-]?key|secret|token)\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{20,}"),
)
ABSOLUTE_PATH = re.compile(rb"(?i)(?:[A-Z]:\\Users\\|/home/|/Users/)")
ZIP_TIME = (1980, 1, 1, 0, 0, 0)


class ReleaseValidationError(RuntimeError):
    pass


@dataclass(frozen=True)
class Artifact:
    name: str
    size: int
    sha256: str


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_payload(root: str | Path) -> list[Path]:
    base = Path(root).resolve()
    files: list[Path] = []
    issues: list[str] = []
    for path in sorted(base.rglob("*"), key=lambda item: item.as_posix().lower()):
        if path.is_symlink():
            issues.append(f"symlink:{path.relative_to(base).as_posix()}")
            continue
        if not path.is_file():
            continue
        rel = path.relative_to(base)
        lowered = {part.lower() for part in rel.parts}
        if path.name.lower() in FORBIDDEN_NAMES or lowered & FORBIDDEN_PARTS:
            issues.append(f"forbidden:{rel.as_posix()}")
            continue
        data = path.read_bytes()
        if any(pattern.search(data) for pattern in SECRET_PATTERNS):
            issues.append(f"secret:{rel.as_posix()}")
        if ABSOLUTE_PATH.search(data):
            issues.append(f"absolute_path:{rel.as_posix()}")
        files.append(path)
    if issues:
        raise ReleaseValidationError("; ".join(issues))
    return files


def create_reproducible_zip(source: str | Path, destination: str | Path, *, portable: bool = True) -> Path:
    source_path, target = Path(source).resolve(), Path(destination)
    files = validate_payload(source_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        if portable:
            marker = zipfile.ZipInfo(".portable", ZIP_TIME)
            marker.external_attr = 0o100644 << 16
            archive.writestr(marker, b"jarvis.portable.v1\n")
        for path in files:
            info = zipfile.ZipInfo(path.relative_to(source_path).as_posix(), ZIP_TIME)
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    return target


def generate_sbom(destination: str | Path, packages: Iterable[metadata.PackageMetadata] | None = None) -> Path:
    components = []
    distributions = packages if packages is not None else (dist.metadata for dist in metadata.distributions())
    for package in distributions:
        name, version = package.get("Name"), package.get("Version")
        if name and version:
            components.append({"type": "library", "name": name, "version": version, "purl": f"pkg:pypi/{name.lower()}@{version}"})
    value = {"bomFormat": "CycloneDX", "specVersion": "1.5", "version": 1, "components": sorted(components, key=lambda row: (row["name"].lower(), row["version"]))}
    target = Path(destination)
    target.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    return target


def write_release_metadata(release_dir: str | Path, *, version: str, notes: str, channel: str = "stable", published_at: str | None = None) -> tuple[Path, Path, Path]:
    root = Path(release_dir)
    root.mkdir(parents=True, exist_ok=True)
    notes_path = root / "RELEASE_NOTES.md"
    notes_path.write_text(notes.rstrip() + "\n", encoding="utf-8")
    artifacts = [Artifact(path.name, path.stat().st_size, sha256_file(path)) for path in sorted(root.iterdir()) if path.is_file() and path.name not in {"SHA256SUMS.txt", "release-manifest.json"}]
    manifest = {
        "schema_version": 1,
        "application_version": version,
        "channel": channel,
        "published_at": published_at or datetime.now(timezone.utc).isoformat(),
        "artifacts": [item.__dict__ for item in artifacts],
        "install_modes": ["user", "system", "portable", "repair", "update", "uninstall"],
        "data_policy": "preserve_by_default",
    }
    manifest_path = root / "release-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    checksum_path = root / "SHA256SUMS.txt"
    checksum_targets = [*artifacts, Artifact(manifest_path.name, manifest_path.stat().st_size, sha256_file(manifest_path))]
    checksum_path.write_text("".join(f"{item.sha256}  {item.name}\n" for item in sorted(checksum_targets, key=lambda row: row.name)), encoding="ascii")
    return notes_path, manifest_path, checksum_path


def verify_checksums(release_dir: str | Path) -> bool:
    root = Path(release_dir)
    for line in (root / "SHA256SUMS.txt").read_text(encoding="ascii").splitlines():
        digest, name = line.split("  ", 1)
        if sha256_file(root / name) != digest:
            return False
    return True


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    zip_command = commands.add_parser("zip")
    zip_command.add_argument("source")
    zip_command.add_argument("destination")
    scan_command = commands.add_parser("scan")
    scan_command.add_argument("source")
    sbom_command = commands.add_parser("sbom")
    sbom_command.add_argument("destination")
    metadata_command = commands.add_parser("metadata")
    metadata_command.add_argument("release_dir")
    metadata_command.add_argument("--version", required=True)
    metadata_command.add_argument("--notes-file", required=True)
    args = parser.parse_args(argv)
    if args.command == "zip":
        create_reproducible_zip(args.source, args.destination)
    elif args.command == "scan":
        validate_payload(args.source)
    elif args.command == "sbom":
        generate_sbom(args.destination)
    else:
        notes = Path(args.notes_file).read_text(encoding="utf-8")
        write_release_metadata(args.release_dir, version=args.version, notes=notes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
