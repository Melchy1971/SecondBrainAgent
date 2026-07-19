from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.ci_gate import (
    GateError,
    changed_python_files,
    check_changed_installer_types,
    check_secrets,
    check_tag,
    check_workflows,
)


WORKFLOWS = {
    "pull-request.yml", "main-validation.yml", "security.yml", "nightly.yml",
    "release-candidate.yml", "release.yml",
}


def _git_repo(path: Path) -> Path:
    path.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    return path


def _commit(root: Path, message: str) -> str:
    safe = f"safe.directory={root.resolve()}"
    subprocess.run(["git", "-c", safe, "add", "."], cwd=root, check=True)
    subprocess.run(
        [
            "git", "-c", safe, "-c", "user.name=CI", "-c", "user.email=ci@example.invalid",
            "commit", "-qm", message,
        ],
        cwd=root,
        check=True,
    )
    return subprocess.run(
        ["git", "-c", safe, "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def test_all_workflows_exist_and_actions_are_sha_pinned():
    root = Path(__file__).resolve().parents[1]
    present = {path.name for path in (root / ".github/workflows").glob("*.yml")}
    assert WORKFLOWS <= present
    check_workflows(root)


def test_release_tag_must_equal_project_version(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "31.3.0"\n', encoding="utf-8")
    check_tag("v31.3.0", tmp_path)
    with pytest.raises(GateError, match="tag_version_mismatch"):
        check_tag("v31.3.1", tmp_path)


def test_secret_gate_blocks_real_tracked_secret(tmp_path: Path):
    root = _git_repo(tmp_path / "repo")
    (root / "app.py").write_text('api_key="actual-production-key-123456789"\n', encoding="utf-8")
    subprocess.run(["git", "-c", f"safe.directory={root}", "add", "app.py"], cwd=root, check=True)
    with pytest.raises(GateError, match="potential_secrets: app.py"):
        check_secrets(root)


def test_changed_python_files_excludes_untouched_baseline_debt(tmp_path: Path):
    root = _git_repo(tmp_path / "repo")
    (root / "SecondBrain").mkdir()
    (root / "scripts").mkdir()
    (root / "SecondBrain" / "legacy.py").write_text("x = 1; y = 2\n", encoding="utf-8")
    base = _commit(root, "baseline")
    (root / "scripts" / "changed.py").write_text("value = 1\n", encoding="utf-8")
    (root / "README.md").write_text("changed\n", encoding="utf-8")
    _commit(root, "change")

    assert changed_python_files(base, root) == ["scripts/changed.py"]


def test_installer_type_check_ignores_unchanged_baseline(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("scripts.ci_gate.changed_python_files", lambda base, root: ["scripts/changed.py"])
    calls = []
    monkeypatch.setattr("scripts.ci_gate.subprocess.run", lambda *args, **kwargs: calls.append(args))

    check_changed_installer_types("base", tmp_path)

    assert calls == []


def test_release_requires_signed_tag_gate_environment_and_payloads():
    root = Path(__file__).resolve().parents[1]
    release = (root / ".github/workflows/release.yml").read_text(encoding="utf-8")
    candidate = (root / ".github/workflows/release-candidate.yml").read_text(encoding="utf-8")
    assert ".verification.verified" in release
    assert "environment: stable-release" in release
    assert "needs: artifacts" in release
    assert "SHA256SUMS.txt" in release and "sbom.cdx.json" in release
    assert "build.ps1" in candidate and "attest-build-provenance" in candidate
    assert "if-no-files-found: error" in candidate


def test_pr_does_not_package_and_main_has_supported_matrix():
    root = Path(__file__).resolve().parents[1]
    pull_request = (root / ".github/workflows/pull-request.yml").read_text(encoding="utf-8")
    main = (root / ".github/workflows/main-validation.yml").read_text(encoding="utf-8")
    assert "build.ps1" not in pull_request and "PyInstaller" not in pull_request
    assert "fetch-depth: 0" in pull_request
    assert "ci_gate.py lint-diff" in pull_request
    assert "ci_gate.py type-diff" in pull_request
    assert "ruff check SecondBrain scripts tests" not in pull_request
    assert "mypy --ignore-missing-imports SecondBrain/install" not in pull_request
    assert "ubuntu-24.04" in main and "windows-2025" in main
    assert '["3.12", "3.13"]' in main
