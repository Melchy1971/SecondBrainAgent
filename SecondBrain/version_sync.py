"""Propagate the single source-of-truth version into docs (idempotent).

Reads the canonical version (pyproject via secondbrain.version) and rewrites the
derived anchors: docs/09_MASTERPLAN_STATUS.json and the README title line. Does not
touch historical version references in prose.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from secondbrain.version import get_version, get_build_number


def sync_version(project_root: str | Path = ".") -> dict:
    root = Path(project_root)
    version = get_version()
    build = get_build_number(version)
    updated: dict[str, str] = {}

    masterplan = root / "docs" / "09_MASTERPLAN_STATUS.json"
    if masterplan.exists():
        with masterplan.open("r", encoding="utf-8", newline="") as stream:
            old_text = stream.read()
        data = json.loads(old_text)
        data["version"] = version
        data["current_version"] = f"v{version}"
        data["build"] = build
        data["version_source"] = "pyproject.toml"
        new_text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        if new_text != old_text:
            masterplan.write_text(new_text, encoding="utf-8", newline="\n")
            updated["masterplan"] = version

    readme = root / "README.md"
    if readme.exists():
        with readme.open("r", encoding="utf-8", newline="") as stream:
            text = stream.read()
        new = text
        new = re.sub(r"(?m)^(#\s+SecondBrain-Agent\s+v)[0-9][^\s]*", rf"\g<1>{version}", new, count=1)
        new = re.sub(
            r"\([0-9]+\.[0-9]+(?:\.[0-9]+)?\s*->\s*Build\s*[0-9]+\)",
            f"({version} -> Build {build})",
            new,
            count=1,
        )
        new = re.sub(
            r"(?m)^(Aktueller\s+dokumentierter\s+Stand:\s*)v[0-9]+(?:\.[0-9]+){1,2}",
            rf"\g<1>v{version}",
            new,
            count=1,
        )
        if new != text:
            readme.write_text(new, encoding="utf-8", newline="\n")
            updated["readme"] = version

    return {"version": version, "build": build, "updated": updated}
