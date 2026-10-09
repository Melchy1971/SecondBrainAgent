import json
import re
import subprocess
from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _git_available(root: Path) -> bool:
    try:
        subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(root), check=True, capture_output=True)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False  # z. B. Quell-Tarball ohne .git


def _is_ancestor_of_head(root: Path, commit: str) -> bool:
    result = subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], check=False,
                            cwd=str(root), capture_output=True)
    return result.returncode == 0


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
        "package_version",
        "documented_feature_level",
        "inventoried_commit",
        "verified_commit",
        "live_evidence",
        "release_state",
    }
    assert required_fields.issubset(masterplan.keys())

    # No stale pre-v30.61 focus schema.
    for stale in ("status", "focus", "last_delta", "native_desktop", "new_commands"):
        assert stale not in masterplan

    assert masterplan["version"] == version
    assert masterplan["current_version"] == f"v{version}"
    assert masterplan["package_version"] == version

    header = readme.splitlines()[2]
    assert header == f"# SecondBrain-Agent v{version}"

    expected_releases = [f"v30.{n}" for n in range(61, 78)]
    release_headings = _release_versions_61_to_77(notes)
    assert set(expected_releases).issubset(set(release_headings))

    completed_releases = {item.get("release") for item in masterplan["completed_capabilities"] if isinstance(item, dict)}
    assert set(expected_releases).issubset(completed_releases)

    for blocker in masterplan["remaining_blockers"]:
        assert "v30.46" not in str(blocker)

    # Validate distinct status model and separation
    allowed_states = {
        "planned",
        "implemented",
        "verified_hermetic",
        "verified_integration",
        "live_certified",
        "released",
        "deprecated",
        "blocked",
    }
    
    assert masterplan["release_state"] in allowed_states
    
    # Inventarisierte/verifizierte Commits muessen real und Teil der Historie
    # von HEAD sein. Gleichheit mit HEAD ist nicht erfuellbar: jeder Commit, der
    # diese Datei mitnimmt, erzeugt einen neuen HEAD.
    if _git_available(root):
        for field in ("inventoried_commit", "verified_commit"):
            commit = masterplan[field]
            assert re.fullmatch(r"[0-9a-f]{40}", commit), f"{field} ist kein vollstaendiger Commit-Hash: {commit!r}"
            assert _is_ancestor_of_head(root, commit), (
                f"{field} ({commit}) ist kein Vorgaenger von HEAD (unbekannter oder fremder Commit)"
            )

    # Validate each capability status
    for item in masterplan["completed_capabilities"]:
        status = item.get("status")
        assert status in allowed_states, (
            f"Capability {item.get('release')} uses invalid status {status!r}. "
            f"Allowed states: {allowed_states}"
        )
        # Ensure no completed placeholder is used
        assert status != "completed", f"Capability {item.get('release')} uses obsolete 'completed' status"
        assert status != "completed_on_main", f"Capability {item.get('release')} uses obsolete 'completed_on_main' status"
