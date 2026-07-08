"""Single source of truth for the project version.

Resolution order:
1. Installed package metadata (``secondbrain-agent``) when running as an installed dist.
2. The nearest ``pyproject.toml`` (``[project].version``) when running from source.

Everything else (launcher, GUI, CLI, docs sync) reads from here. The build number
is derived deterministically from the version, so it too originates from pyproject.
"""

from __future__ import annotations

import re
from pathlib import Path

PACKAGE_NAME = "secondbrain-agent"
_FALLBACK = "0.0.0"


def _read_pyproject_version() -> str | None:
    for base in [Path(__file__).resolve().parent, *Path(__file__).resolve().parents]:
        pp = base / "pyproject.toml"
        if not pp.exists():
            continue
        text = pp.read_text(encoding="utf-8")
        try:
            import tomllib  # Python 3.11+
            version = tomllib.loads(text).get("project", {}).get("version")
            if version:
                return str(version)
        except Exception:
            pass
        match = re.search(r'(?m)^\s*version\s*=\s*["\']([^"\']+)["\']', text)
        if match:
            return match.group(1)
    return None


def get_version() -> str:
    """Return the canonical version string.

    pyproject.toml is the leading source. Installed-package metadata is only a
    fallback for when the source tree (and thus pyproject) is not present.
    """
    from_pyproject = _read_pyproject_version()
    if from_pyproject:
        return from_pyproject
    try:
        from importlib.metadata import version
        meta = version(PACKAGE_NAME)
        if meta:
            return meta
    except Exception:
        pass
    return _FALLBACK


def version_tuple(version: str | None = None) -> tuple[int, int, int]:
    raw = version or get_version()
    parts = re.split(r"[.\-+]", raw)
    nums: list[int] = []
    for part in parts:
        if part.isdigit():
            nums.append(int(part))
        else:
            break
    while len(nums) < 3:
        nums.append(0)
    return (nums[0], nums[1], nums[2])


def get_build_number(version: str | None = None) -> int:
    """Deterministic build number derived from the pyproject version.

    30.61.0 -> 306100 (major*10000 + minor*100 + patch).
    """
    major, minor, patch = version_tuple(version)
    return major * 10000 + minor * 100 + patch


def version_info() -> dict:
    v = get_version()
    major, minor, patch = version_tuple(v)
    return {
        "version": v,
        "build": get_build_number(v),
        "major": major,
        "minor": minor,
        "patch": patch,
        "package": PACKAGE_NAME,
        "source": "pyproject.toml / package metadata",
    }


__version__ = get_version()
__build__ = get_build_number()
