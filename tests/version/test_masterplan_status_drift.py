import json
import re
from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _release_versions_61_to_77(notes_text: str) -> list[str]:
    matches = re.findall(r"(?m)^#\s+Release Notes\s+v30\.(\d+)\b", notes_text)
    ordered = []
    for m in matches:
        n = int(m)
        if 61 <= n <= 77:
            ordered.append(f"v30.{n}")
    return ordered


def test_masterplan_version_and_schema_consistency():
    root = _root()
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    notes = (root / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")
    masterplan = json.loads((root / "docs" / "09_MASTERPLAN_STATUS.json").read_text(encoding="utf-8"))

    version_match = re.search(r"(?m)^\s*version\s*=\s*\"([^\"]+)\"", pyproject)
    assert version_match, "pyproject version missing"
    version = version_match.group(1)

    required_fields = {
        "version",
        "current_version",
        "completed_capabilities",
        "remaining_blockers",
        "degraded_modes",
        "next_sprint",
        "release_readiness",
    }
    assert required_fields.issubset(masterplan.keys())

    # No stale pre-v30.61 focus schema.
    for stale in ("status", "focus", "last_delta", "native_desktop", "new_commands"):
        assert stale not in masterplan

    assert masterplan["version"] == version
    assert masterplan["current_version"] == f"v{version}"

    header = readme.splitlines()[2]
    assert header == f"# SecondBrain-Agent v{version}"
    assert f"Aktueller dokumentierter Stand: v{version}" in readme

    expected_releases = [f"v30.{n}" for n in range(61, 78)]
    release_headings = _release_versions_61_to_77(notes)
    assert set(expected_releases).issubset(set(release_headings))

    completed_releases = {item.get("release") for item in masterplan["completed_capabilities"] if isinstance(item, dict)}
    assert set(expected_releases).issubset(completed_releases)

    for blocker in masterplan["remaining_blockers"]:
        assert "v30.46" not in str(blocker)
