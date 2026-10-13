"""Commit-gebundene Nachweise ohne eigenes Fach-Gate.

* ``full_pytest``        -- vollstaendiger pytest-Lauf, ausgewertet ueber JUnit-XML.
* ``version_sync``       -- Masterplan-Version gleich Paketversion (pyproject).
* ``ci_current_commit``  -- GitHub-Check-Runs genau des aktuellen Commits.

Jeder Bericht wird ueber :mod:`secondbrain.release.evidence` versiegelt. Externe
Aufrufe (pytest, gh) laufen ueber einen injizierbaren ``runner``.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Callable, Mapping
from uuid import uuid4

from secondbrain.release.evidence import git_commit, seal

PASS, FAIL, BLOCKED = "PASS", "FAIL", "BLOCKED"
REPORTS = Path("runtime/reports")
FULL_PYTEST_SCHEMA = "secondbrain.full_pytest.v1"
VERSION_SYNC_SCHEMA = "secondbrain.version_sync.v1"
CI_COMMIT_SCHEMA = "secondbrain.ci_current_commit.v1"

Runner = Callable[..., Any]


def _write(root: Path, name: str, report: dict[str, Any]) -> dict[str, Any]:
    target = root / REPORTS / name
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
    temporary.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, target)
    return {**report, "report": (REPORTS / name).as_posix()}


# --------------------------------------------------------------------------
# Vollstaendige Testsuite
# --------------------------------------------------------------------------

# pytest-Exit-Codes: 0 alle bestanden, 1 Tests fehlgeschlagen. Alles andere
# (2 abgebrochen, 3 interner Fehler, 4 Bedienfehler, 5 keine Tests) ist kein
# vollstaendiger Lauf.
_COMPLETE_EXIT_CODES = {0, 1}


def _junit_totals(path: Path) -> dict[str, int]:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    for suite in suites:
        for key in totals:
            totals[key] += int(suite.get(key, 0) or 0)
    return totals


def run_full_pytest_evidence(
    project_root: str | Path = ".",
    *,
    env: Mapping[str, str] | None = None,
    runner: Runner = subprocess.run,
    pytest_args: tuple[str, ...] = (),
    write_report: bool = True,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    junit = root / REPORTS / f".full_pytest.{uuid4().hex}.xml"
    junit.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = runner(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={junit}", *pytest_args],
            cwd=root, capture_output=True, text=True, check=False,
        )
        exit_code = int(result.returncode)
        totals = _junit_totals(junit) if junit.is_file() else None
    finally:
        junit.unlink(missing_ok=True)
    complete = totals is not None and exit_code in _COMPLETE_EXIT_CODES and totals["tests"] > 0
    totals = totals or {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    passed = totals["tests"] - totals["failures"] - totals["errors"] - totals["skipped"]
    ok = complete and totals["failures"] == 0 and totals["errors"] == 0
    report = seal({
        "status": PASS if ok else FAIL, "complete": complete, "exit_code": exit_code,
        "total": totals["tests"], "passed": passed, "failed": totals["failures"],
        "errors": totals["errors"], "skipped": totals["skipped"],
        "pytest_args": list(pytest_args),
    }, schema=FULL_PYTEST_SCHEMA, root=root, env=env)
    return _write(root, "full_pytest.json", report) if write_report else report


# --------------------------------------------------------------------------
# Versionssynchronisation
# --------------------------------------------------------------------------


def run_version_sync_evidence(
    project_root: str | Path = ".",
    *,
    env: Mapping[str, str] | None = None,
    write_report: bool = True,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    match = re.search(r'(?m)^\s*version\s*=\s*"([^"]+)"', (root / "pyproject.toml").read_text(encoding="utf-8"))
    package = match.group(1) if match else None
    masterplan = json.loads((root / "docs" / "09_MASTERPLAN_STATUS.json").read_text(encoding="utf-8"))
    fields = {
        "version": masterplan.get("version"),
        "package_version": masterplan.get("package_version"),
        "current_version": masterplan.get("current_version"),
    }
    synchronized = bool(package) and fields["version"] == package and fields["package_version"] == package \
        and fields["current_version"] == f"v{package}"
    report = seal({
        "status": PASS if synchronized else FAIL, "synchronized": synchronized,
        "package_version": package, "masterplan_version": fields["version"], "masterplan_fields": fields,
    }, schema=VERSION_SYNC_SCHEMA, root=root, env=env)
    return _write(root, "version_sync.json", report) if write_report else report


# --------------------------------------------------------------------------
# CI fuer genau diesen Commit
# --------------------------------------------------------------------------

# Nur echte Erfolge zaehlen; "skipped"/"neutral" belegen nichts.
_SUCCESS = {"success"}


def _github_repo(root: Path, runner: Runner) -> str | None:
    result = runner(["git", "remote", "get-url", "origin"], cwd=root, capture_output=True, text=True, check=False)
    match = re.search(r"github\.com[:/]([^/\s]+/[^/\s]+?)(?:\.git)?\s*$", str(result.stdout or ""))
    return match.group(1) if match else None


def run_ci_commit_evidence(
    project_root: str | Path = ".",
    *,
    runner: Runner = subprocess.run,
    write_report: bool = True,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    commit = git_commit(root)
    repo = _github_repo(root, runner)
    checks: list[dict[str, str]] = []
    conclusion = "unavailable"
    if commit and repo:
        result = runner(
            ["gh", "api", f"repos/{repo}/commits/{commit}/check-runs", "--paginate",
             "--jq", ".check_runs[] | {name, status, conclusion}"],
            cwd=root, capture_output=True, text=True, check=False,
        )
        if result.returncode == 0:
            for line in str(result.stdout or "").splitlines():
                row = json.loads(line)
                checks.append({"name": str(row.get("name")), "status": str(row.get("status")),
                               "conclusion": str(row.get("conclusion"))})
            if not checks:
                conclusion = "no_checks"          # z. B. Commit nicht gepusht
            elif any(c["status"] != "completed" for c in checks):
                conclusion = "pending"
            elif all(c["conclusion"] in _SUCCESS for c in checks):
                conclusion = "success"
            else:
                conclusion = "failure"
        else:
            conclusion = "not_found"
    # Die Fakten stammen aus der CI selbst -- unabhaengig davon, wo abgefragt wird.
    report = seal({
        "status": PASS if conclusion == "success" else FAIL, "conclusion": conclusion,
        "checked_commit": commit, "repository": repo, "checks": checks,
    }, schema=CI_COMMIT_SCHEMA, root=root, environment="ci")
    return _write(root, "ci_current_commit.json", report) if write_report else report
