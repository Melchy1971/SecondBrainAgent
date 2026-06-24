from __future__ import annotations

from pathlib import Path

from secondbrain.module_registry import ModuleRegistry
from secondbrain.release.repo_doctor import run_repo_doctor


PYPROJECT = """[build-system]
requires = [\"setuptools>=69\", \"wheel\"]
build-backend = \"setuptools.build_meta\"

[project]
name = \"secondbrain-agent\"
version = \"18.11.0\"
requires-python = \">=3.11\"
dependencies = []

[project.optional-dependencies]
dev = [\"pytest>=8.0.0\"]

[project.scripts]
secondbrain = \"launcher:main\"

[tool.setuptools.packages.find]
include = [\"secondbrain\", \"secondbrain.*\"]
"""


def _write_minimal_project(root: Path) -> None:
    (root / "secondbrain").mkdir(parents=True)
    (root / "secondbrain" / "release").mkdir(parents=True)
    (root / "docs").mkdir(parents=True)
    (root / "secondbrain" / "module_registry.py").write_text("", encoding="utf-8")
    (root / "secondbrain" / "launcher_runtime_v126.py").write_text("", encoding="utf-8")
    (root / "secondbrain" / "p0_runtime.py").write_text("", encoding="utf-8")
    (root / "secondbrain" / "p1_rag_runtime.py").write_text("", encoding="utf-8")
    (root / "secondbrain" / "release" / "dependency_inventory.py").write_text("", encoding="utf-8")
    (root / "docs" / "RELEASE_WORKFLOW_v18_9.md").write_text("# Release Workflow\n", encoding="utf-8")
    (root / "launcher.py").write_text("print('ok')\n", encoding="utf-8")
    (root / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    (root / "requirements.txt").write_text("# core runtime uses stdlib\n", encoding="utf-8")
    (root / "requirements-dev.txt").write_text("-r requirements.txt\npytest>=8.0.0\n", encoding="utf-8")
    (root / "requirements-runtime.txt").write_text("# Optional feature dependencies are declared in pyproject.toml extras.\n", encoding="utf-8")
    (root / "pytest.ini").write_text("[pytest]\ntestpaths = tests\npythonpath = .\n", encoding="utf-8")
    (root / "README.md").write_text("# SecondBrain-Agent v18.x\n\npython launcher.py health\n\npip install -e \".[dev]\"\n", encoding="utf-8")


def test_repo_doctor_accepts_minimal_valid_project(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)

    report = run_repo_doctor(tmp_path)
    payload = report.to_dict()

    assert payload["ok"] is True
    assert payload["summary"]["error"] == 0
    assert any(check["key"] == "pyproject.toml:[project]" for check in payload["checks"])
    assert any(check["key"] == "requirements-runtime.txt:policy" and check["status"] == "ok" for check in payload["checks"])


def test_repo_doctor_blocks_missing_required_path(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)
    (tmp_path / "launcher.py").unlink()

    report = run_repo_doctor(tmp_path)
    payload = report.to_dict()

    assert payload["ok"] is False
    assert any(check["key"] == "launcher.py" and check["status"] == "error" for check in payload["checks"])


def test_repo_doctor_blocks_deleted_changelog_reference(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)
    (tmp_path / "README.md").write_text("# SecondBrain-Agent v18.x\n\npython launcher.py health\n\nCHANGELOG_*.md\n", encoding="utf-8")

    payload = run_repo_doctor(tmp_path).to_dict()

    assert payload["ok"] is False
    assert any(check["key"] == "README.md:deleted-changelog-reference" and check["status"] == "error" for check in payload["checks"])


def test_repo_doctor_blocks_forbidden_root_artifacts(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)
    (tmp_path / "PATCH_OLD_REPORT.md").write_text("obsolete", encoding="utf-8")

    payload = run_repo_doctor(tmp_path).to_dict()

    assert payload["ok"] is False
    assert any(check["key"] == "repo:forbidden-artifacts" and check["status"] == "error" for check in payload["checks"])


def test_repo_doctor_blocks_pycache_outside_virtualenv(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)
    cache = tmp_path / "secondbrain" / "__pycache__"
    cache.mkdir()
    (cache / "module.cpython-313.pyc").write_bytes(b"cache")

    payload = run_repo_doctor(tmp_path).to_dict()

    assert payload["ok"] is False
    assert any(check["key"] == "repo:forbidden-artifacts" and check["status"] == "error" for check in payload["checks"])


def test_repo_doctor_ignores_virtualenv_cache_artifacts(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)
    cache = tmp_path / ".venv" / "Lib" / "site-packages" / "pkg" / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "module.cpython-313.pyc").write_bytes(b"cache")

    payload = run_repo_doctor(tmp_path).to_dict()

    assert payload["ok"] is True
    assert any(check["key"] == "repo:forbidden-artifacts" and check["status"] == "ok" for check in payload["checks"])


def test_repo_doctor_writes_report(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)

    report = run_repo_doctor(tmp_path, write_report=True)

    assert report.ok is True
    assert (tmp_path / "release" / "repo_doctor_latest.json").exists()


def test_command_index_exposes_repo_doctor() -> None:
    registry = ModuleRegistry()

    assert registry.command_index()["repo-doctor"] == "core"
    assert registry.resolve_command("repo-doctor").key == "core"
