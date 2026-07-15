from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.ci_gate import GateError, check_secrets, check_tag, check_workflows


WORKFLOWS = {
    "pull-request.yml", "main-validation.yml", "security.yml", "nightly.yml",
    "release-candidate.yml", "release.yml",
}


def _git_repo(path: Path) -> Path:
    path.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    return path


def test_all_workflows_exist_and_actions_are_sha_pinned():
    root = Path(__file__).resolve().parents[1]
    assert WORKFLOWS == {path.name for path in (root / ".github/workflows").glob("*.yml")}
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
    assert "ubuntu-24.04" in main and "windows-2025" in main
    assert '["3.12", "3.13"]' in main
