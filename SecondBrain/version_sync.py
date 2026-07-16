"""Propagate the single source-of-truth version into docs (idempotent).

Reads the canonical version (pyproject via secondbrain.version) and rewrites the
derived anchors: docs/09_MASTERPLAN_STATUS.json and the README title line. Does not
touch historical version references in prose or reformat unrelated JSON content.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from secondbrain.version import get_version, get_build_number


def _replace_json_scalar(text: str, key: str, value: str | int) -> tuple[str, bool]:
    """Replace the first JSON scalar for *key* without reformatting the file."""
    encoded = json.dumps(value, ensure_ascii=False)
    pattern = re.compile(rf'("{re.escape(key)}"\s*:\s*)("(?:[^"\\]|\\.)*"|-?\d+(?:\.\d+)?)')
    updated, count = pattern.subn(rf"\g<1>{encoded}", text, count=1)
    return updated, bool(count)


def _insert_json_scalars(text: str, values: dict[str, str | int]) -> str:
    """Append missing top-level scalars while retaining the existing indentation."""
    closing = text.rfind("}")
    if closing < 0:
        raise ValueError("masterplan JSON object is missing its closing brace")
    prefix = text[:closing].rstrip()
    suffix = text[closing:]
    indent_match = re.search(r'(?m)^([ \t]+)"', text)
    indent = indent_match.group(1) if indent_match else "  "
    if prefix and prefix[-1] != "{":
        if not prefix.endswith(","):
            prefix += ","
        prefix += "\n"
    entries = [
        f"{indent}{json.dumps(key)}: {json.dumps(value, ensure_ascii=False)}"
        for key, value in values.items()
    ]
    return prefix + ",\n".join(entries) + "\n" + suffix


def _sync_masterplan_text(text: str, *, version: str, build: int) -> str:
    """Update generated top-level anchors while preserving unrelated formatting."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    updated = normalized
    missing: dict[str, str | int] = {}
    for key, value in (
        ("version", version),
        ("current_version", f"v{version}"),
        ("build", build),
        ("version_source", "pyproject.toml"),
    ):
        updated, found = _replace_json_scalar(updated, key, value)
        if not found:
            missing[key] = value

    if missing:
        json.loads(updated)
        updated = _insert_json_scalars(updated, missing)
        if not updated.endswith("\n"):
            updated += "\n"
    elif updated and not updated.endswith("\n"):
        updated += "\n"
    return updated


def sync_version(project_root: str | Path = ".") -> dict:
    root = Path(project_root)
    version = get_version()
    build = get_build_number(version)
    updated: dict[str, str] = {}

    masterplan = root / "docs" / "09_MASTERPLAN_STATUS.json"
    if masterplan.exists():
        with masterplan.open("r", encoding="utf-8", newline="") as stream:
            old_text = stream.read()
        new_text = _sync_masterplan_text(old_text, version=version, build=build)
        if new_text != old_text:
            masterplan.write_text(new_text, encoding="utf-8", newline="\n")
            updated["masterplan"] = version

    readme = root / "README.md"
    if readme.exists():
        with readme.open("r", encoding="utf-8", newline="") as stream:
            text = stream.read()
        new = text.replace("\r\n", "\n").replace("\r", "\n")
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
