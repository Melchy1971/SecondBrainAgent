"""full_pytest, version_sync und ci_current_commit mit simulierten Werkzeugen."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from secondbrain.release import evidence_producers as producers
from secondbrain.release import jarvis_1_0_gate as aggregator


class _Result:
    def __init__(self, returncode: int = 0, stdout: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout


def _pytest_runner(exit_code: int, xml: str | None):
    def run(args, **_kwargs):
        junit = Path(next(a for a in args if a.startswith("--junitxml=")).split("=", 1)[1])
        if xml is not None:
            junit.write_text(xml, encoding="utf-8")
        return _Result(exit_code)
    return run


SUITE = '<testsuites><testsuite tests="{t}" failures="{f}" errors="{e}" skipped="{s}"/></testsuites>'


@pytest.mark.parametrize("exit_code,counts,status,complete", [
    (0, (100, 0, 0, 4), "PASS", True),
    (1, (100, 2, 0, 0), "FAIL", True),
    (1, (100, 0, 1, 0), "FAIL", True),
    (2, (40, 0, 0, 0), "FAIL", False),      # abgebrochen
    (5, (0, 0, 0, 0), "FAIL", False),       # keine Tests
])
def test_full_pytest_evaluates_junit(tmp_path: Path, exit_code, counts, status, complete) -> None:
    t, f, e, s = counts
    report = producers.run_full_pytest_evidence(
        tmp_path, env={}, runner=_pytest_runner(exit_code, SUITE.format(t=t, f=f, e=e, s=s)), write_report=False)
    assert (report["status"], report["complete"]) == (status, complete)
    assert (report["failed"], report["errors"], report["skipped"]) == (f, e, s)
    assert aggregator._criterion_passes("full_test_suite", report) is (status == "PASS")


def test_full_pytest_without_junit_is_incomplete(tmp_path: Path) -> None:
    report = producers.run_full_pytest_evidence(tmp_path, env={}, runner=_pytest_runner(0, None), write_report=False)
    assert report["complete"] is False and report["status"] == "FAIL"
    assert not list((tmp_path / "runtime" / "reports").glob(".full_pytest.*"))


def test_full_pytest_writes_sealed_report(tmp_path: Path) -> None:
    report = producers.run_full_pytest_evidence(
        tmp_path, env={}, runner=_pytest_runner(0, SUITE.format(t=3, f=0, e=0, s=0)))
    stored = json.loads((tmp_path / report["report"]).read_text(encoding="utf-8"))
    assert stored["schema"] == producers.FULL_PYTEST_SCHEMA and stored["passed"] == 3


def _project(tmp_path: Path, package: str, masterplan: dict) -> Path:
    (tmp_path / "docs").mkdir()
    (tmp_path / "pyproject.toml").write_text(f'[project]\nversion = "{package}"\n', encoding="utf-8")
    (tmp_path / "docs" / "09_MASTERPLAN_STATUS.json").write_text(json.dumps(masterplan), encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize("masterplan,synchronized", [
    ({"version": "1.2.3", "package_version": "1.2.3", "current_version": "v1.2.3"}, True),
    ({"version": "1.2.2", "package_version": "1.2.3", "current_version": "v1.2.3"}, False),
    ({"version": "1.2.3", "package_version": "1.2.3", "current_version": "v1.2.2"}, False),
])
def test_version_sync(tmp_path: Path, masterplan: dict, synchronized: bool) -> None:
    report = producers.run_version_sync_evidence(_project(tmp_path, "1.2.3", masterplan), env={}, write_report=False)
    assert report["synchronized"] is synchronized
    assert aggregator._criterion_passes("masterplan_package_version_sync", report) is synchronized


def _gh_runner(remote: str, gh_code: int, runs: list[dict]):
    def run(args, **_kwargs):
        if args[:2] == ["git", "remote"]:
            return _Result(0, remote + "\n")
        assert args[0] == "gh" and re.match(r"repos/owner/repo/commits/[0-9a-f]+/check-runs", args[2])
        return _Result(gh_code, "\n".join(json.dumps(r) for r in runs))
    return run


@pytest.mark.parametrize("gh_code,runs,conclusion", [
    (0, [{"name": "validate", "status": "completed", "conclusion": "success"}], "success"),
    (0, [{"name": "a", "status": "completed", "conclusion": "success"},
         {"name": "b", "status": "completed", "conclusion": "failure"}], "failure"),
    (0, [{"name": "a", "status": "in_progress", "conclusion": None}], "pending"),
    (0, [{"name": "a", "status": "completed", "conclusion": "skipped"}], "failure"),   # skipped belegt nichts
    (0, [], "no_checks"),
    (1, [], "not_found"),
])
def test_ci_commit_conclusion(tmp_path: Path, monkeypatch, gh_code, runs, conclusion) -> None:
    monkeypatch.setattr(producers, "git_commit", lambda _root: "a" * 40)
    report = producers.run_ci_commit_evidence(
        tmp_path, runner=_gh_runner("git@github.com:owner/repo.git", gh_code, runs), write_report=False)
    assert report["conclusion"] == conclusion
    assert report["environment"] == "ci"
    assert aggregator._criterion_passes("current_commit_ci_verified", report) is (conclusion == "success")


@pytest.mark.parametrize("remote", ["https://github.com/owner/repo.git", "https://github.com/owner/repo",
                                    "git@github.com:owner/repo.git"])
def test_github_remote_parsing(tmp_path: Path, remote: str) -> None:
    assert producers._github_repo(tmp_path, lambda *a, **k: _Result(0, remote + "\n")) == "owner/repo"


def test_non_github_remote_is_unavailable(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(producers, "git_commit", lambda _root: "a" * 40)
    report = producers.run_ci_commit_evidence(
        tmp_path, runner=lambda *a, **k: _Result(0, "https://gitlab.example/x/y.git"), write_report=False)
    assert report["conclusion"] == "unavailable" and report["status"] == "FAIL"
