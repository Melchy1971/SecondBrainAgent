from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class BuildInfo:
    version: str
    build_id: str
    created_at_utc: str
    source_hash: str
    git_commit: str | None = None
    environment: str = "local"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def calculate_source_hash(root: str | Path, *, include_suffixes: tuple[str, ...] = (".py", ".md", ".ini", ".toml", ".json")) -> str:
    base = Path(root)
    digest = hashlib.sha256()
    if not base.exists():
        raise FileNotFoundError(str(base))
    for path in sorted(p for p in base.rglob("*") if p.is_file() and p.suffix in include_suffixes):
        rel = path.relative_to(base).as_posix()
        if any(part in {".git", "__pycache__", ".pytest_cache"} for part in path.parts):
            continue
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def create_build_info(root: str | Path, *, version: str, environ: Mapping[str, str] | None = None) -> BuildInfo:
    env = environ or os.environ
    source_hash = calculate_source_hash(root)
    commit = env.get("GIT_COMMIT") or env.get("CI_COMMIT_SHA")
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    build_seed = f"{version}|{source_hash}|{commit or ''}"
    build_id = hashlib.sha256(build_seed.encode("utf-8")).hexdigest()[:16]
    return BuildInfo(
        version=version,
        build_id=build_id,
        created_at_utc=created_at,
        source_hash=source_hash,
        git_commit=commit,
        environment=env.get("SECOND_BRAIN_ENV", "local"),
    )


def write_build_info(root: str | Path, *, version: str, output_path: str | Path = "release/build.json") -> Path:
    base = Path(root)
    info = create_build_info(base, version=version)
    target = base / output_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(info.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return target
