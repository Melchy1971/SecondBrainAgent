import json
import re
from pathlib import Path

import secondbrain
from secondbrain import version as V
from secondbrain.version_sync import sync_version
from secondbrain.gui.version import APP_VERSION
from secondbrain.cli.version import CLI_VERSION


def _pyproject_version() -> str:
    text = Path(V.__file__).resolve().parent.parent.joinpath("pyproject.toml").read_text(encoding="utf-8")
    return re.search(r'(?m)^\s*version\s*=\s*["\']([^"\']+)["\']', text).group(1)


def test_get_version_matches_pyproject():
    assert V.get_version() == _pyproject_version()
    assert re.match(r"^\d+\.\d+\.\d+$", V.get_version())


def test_pyproject_is_leading_source_even_with_stale_metadata():
    # metadata may return None/stale; get_version must still reflect pyproject
    assert V.get_version() == V._read_pyproject_version()


def test_build_number_is_derived_from_version():
    assert V.get_build_number("30.77.0") == 307700
    assert V.version_tuple("30.77.0") == (30, 77, 0)
    assert V.get_build_number() == V.get_build_number(V.get_version())


def test_all_components_share_one_version():
    v = V.get_version()
    assert secondbrain.__version__ == v
    assert APP_VERSION == v
    assert CLI_VERSION == v


def test_version_info_shape():
    info = V.version_info()
    assert info["version"] == V.get_version()
    assert info["build"] == V.get_build_number()
    assert info["package"] == "secondbrain-agent"


def _make_project(tmp_path, old="30.00"):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "09_MASTERPLAN_STATUS.json").write_text(
        json.dumps({"version": old, "current_version": f"v{old}", "status": "IN_PROGRESS",
                    "focus": "keep me"}, indent=2), encoding="utf-8")
    (tmp_path / "README.md").write_text(
        (
            f"# SecondBrain-Agent v{old}\n\n"
            f"Build sample ({old} -> Build 300000).\n"
            f"Aktueller dokumentierter Stand: v{old} Demo.\n\n"
            "since v30.25 stuff\n"
        ),
        encoding="utf-8",
    )


def test_sync_updates_masterplan_and_readme(tmp_path):
    _make_project(tmp_path)
    result = sync_version(tmp_path)
    v = V.get_version()
    data = json.loads((tmp_path / "docs" / "09_MASTERPLAN_STATUS.json").read_text())
    assert data["version"] == v and data["current_version"] == f"v{v}"
    assert data["version_source"] == "pyproject.toml"
    assert data["focus"] == "keep me"          # other keys preserved
    readme = (tmp_path / "README.md").read_text()
    assert readme.splitlines()[0] == f"# SecondBrain-Agent v{v}"
    assert f"({v} -> Build {V.get_build_number(v)})" in readme
    assert f"Aktueller dokumentierter Stand: v{v}" in readme
    assert "since v30.25 stuff" in readme       # historical refs untouched
    assert result["updated"]["masterplan"] == v


def test_sync_is_idempotent(tmp_path):
    _make_project(tmp_path)
    first = sync_version(tmp_path)
    before = (tmp_path / "docs" / "09_MASTERPLAN_STATUS.json").read_text()
    second = sync_version(tmp_path)
    after = (tmp_path / "docs" / "09_MASTERPLAN_STATUS.json").read_text()
    assert second["updated"] == {}
    assert before == after and first["version"] == V.get_version()


def test_sync_normalizes_generated_files_to_lf(tmp_path):
    _make_project(tmp_path)
    masterplan = tmp_path / "docs" / "09_MASTERPLAN_STATUS.json"
    masterplan.write_bytes(masterplan.read_bytes().replace(b"\n", b"\r\n"))
    sync_version(tmp_path)
    assert b"\r\n" not in masterplan.read_bytes()
