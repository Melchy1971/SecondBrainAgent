from __future__ import annotations

from pathlib import Path

from secondbrain.module_registry import ModuleRegistry
from secondbrain.release.repo_doctor import run_repo_doctor


def _write_minimal_project(root: Path) -> None:
    (root / "secondbrain").mkdir(parents=True)
    (root / "secondbrain" / "release").mkdir(parents=True)
    (root / "secondbrain" / "module_registry.py").write_text("", encoding="utf-8")
    (root / "secondbrain" / "launcher_runtime_v126.py").write_text("", encoding="utf-8")
    (root / "secondbrain" / "p0_runtime.py").write_text("", encoding="utf-8")
    (root / "secondbrain" / "p1_rag_runtime.py").write_text("", encoding="utf-8")
    (root / "launcher.py").write_text("print('ok')\n", encoding="utf-8")
    (root / "requirements.txt").write_text("pytest>=8.0.0\n", encoding="utf-8")
    (root / "pytest.ini").write_text("[pytest]\ntestpaths = tests\npythonpath = .\n", encoding="utf-8")
    (root / "README.md").write_text("# SecondBrain-Agent v12.6\n\npython launcher.py health\n", encoding="utf-8")


def test_repo_doctor_accepts_minimal_valid_project(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)

    report = run_repo_doctor(tmp_path)
    payload = report.to_dict()

    assert payload["ok"] is True
    assert payload["summary"]["error"] == 0
    assert payload["summary"]["warning"] == 1
    assert any(check["key"] == "requirements.txt:runtime-dependencies" for check in payload["checks"])


def test_repo_doctor_blocks_missing_required_path(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)
    (tmp_path / "launcher.py").unlink()

    report = run_repo_doctor(tmp_path)
    payload = report.to_dict()

    assert payload["ok"] is False
    assert any(check["key"] == "launcher.py" and check["status"] == "error" for check in payload["checks"])


def test_repo_doctor_writes_report(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)

    report = run_repo_doctor(tmp_path, write_report=True)

    assert report.ok is True
    assert (tmp_path / "release" / "repo_doctor_latest.json").exists()


def test_command_index_exposes_repo_doctor() -> None:
    registry = ModuleRegistry()

    assert registry.command_index()["repo-doctor"] == "core"
    assert registry.resolve_command("repo-doctor").key == "core"
