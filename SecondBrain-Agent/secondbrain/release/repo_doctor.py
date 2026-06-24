from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


REQUIRED_PATHS: tuple[str, ...] = (
    "launcher.py",
    "pyproject.toml",
    "pytest.ini",
    "requirements.txt",
    "requirements-dev.txt",
    "requirements-runtime.txt",
    "README.md",
    "secondbrain/module_registry.py",
    "secondbrain/launcher_runtime_v126.py",
    "secondbrain/p0_runtime.py",
    "secondbrain/p1_rag_runtime.py",
    "secondbrain/release/dependency_inventory.py",
    "docs/RELEASE_WORKFLOW_v18_9.md",
)

EXPECTED_PYTEST_LINES: tuple[str, ...] = (
    "testpaths = tests",
    "pythonpath = .",
)

EXPECTED_PYPROJECT_LINES: tuple[str, ...] = (
    "[build-system]",
    "[project]",
    "name = \"secondbrain-agent\"",
    "requires-python = \">=3.11\"",
    "[project.optional-dependencies]",
    "[project.scripts]",
    "secondbrain = \"launcher:main\"",
    "[tool.setuptools.packages.find]",
)

FORBIDDEN_ROOT_PREFIXES: tuple[str, ...] = (
    "PATCH_",
    "CHANGELOG_",
    "VALIDATION_",
)

IGNORED_ARTIFACT_PARTS: tuple[str, ...] = (
    ".git",
    ".venv",
    "venv",
    "env",
    ".env",
    "build",
    "dist",
    ".eggs",
)

FORBIDDEN_CACHE_PARTS: tuple[str, ...] = (
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
)

FORBIDDEN_FILE_SUFFIXES: tuple[str, ...] = (
    ".pyc",
    ".pyo",
    ".pid",
    ".log",
)

LIGHTWEIGHT_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("health",),
    ("command-index",),
    ("dependency-inventory",),
)


@dataclass(frozen=True)
class DoctorCheck:
    key: str
    status: str
    severity: str
    message: str
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if self.details is None:
            data.pop("details")
        return data


@dataclass(frozen=True)
class RepoDoctorReport:
    ok: bool
    project_root: str
    executed_runtime_checks: bool
    checks: list[DoctorCheck]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "project_root": self.project_root,
            "executed_runtime_checks": self.executed_runtime_checks,
            "summary": summarize_checks(self.checks),
            "checks": [check.to_dict() for check in self.checks],
        }


def summarize_checks(checks: Iterable[DoctorCheck]) -> dict[str, int]:
    summary = {"ok": 0, "warning": 0, "error": 0, "skipped": 0}
    for check in checks:
        summary[check.status] = summary.get(check.status, 0) + 1
    return summary


def _check_required_paths(root: Path) -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []
    for rel in REQUIRED_PATHS:
        path = root / rel
        if path.exists():
            checks.append(DoctorCheck(rel, "ok", "blocking", "required path exists"))
        else:
            checks.append(DoctorCheck(rel, "error", "blocking", "required path missing"))
    return checks


def _check_pytest_ini(root: Path) -> list[DoctorCheck]:
    path = root / "pytest.ini"
    if not path.exists():
        return [DoctorCheck("pytest.ini", "error", "blocking", "pytest.ini missing")]
    content = path.read_text(encoding="utf-8")
    checks: list[DoctorCheck] = []
    for expected in EXPECTED_PYTEST_LINES:
        if expected in content:
            checks.append(DoctorCheck(f"pytest.ini:{expected}", "ok", "blocking", "expected pytest setting present"))
        else:
            checks.append(DoctorCheck(f"pytest.ini:{expected}", "error", "blocking", "expected pytest setting missing"))
    return checks


def _check_pyproject(root: Path) -> list[DoctorCheck]:
    path = root / "pyproject.toml"
    if not path.exists():
        return [DoctorCheck("pyproject.toml", "error", "blocking", "pyproject.toml missing")]
    content = path.read_text(encoding="utf-8")
    checks: list[DoctorCheck] = []
    for expected in EXPECTED_PYPROJECT_LINES:
        if expected in content:
            checks.append(DoctorCheck(f"pyproject.toml:{expected}", "ok", "blocking", "expected pyproject setting present"))
        else:
            checks.append(DoctorCheck(f"pyproject.toml:{expected}", "error", "blocking", "expected pyproject setting missing"))
    return checks


def _check_requirements(root: Path) -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []
    for name in ("requirements.txt", "requirements-dev.txt", "requirements-runtime.txt"):
        path = root / name
        if not path.exists():
            checks.append(DoctorCheck(name, "error", "blocking", f"{name} missing"))
            continue
        content = path.read_text(encoding="utf-8")
        entries = [line.strip() for line in content.splitlines() if line.strip() and not line.strip().startswith("#")]
        checks.append(DoctorCheck(f"{name}:readable", "ok", "blocking", "requirements file readable", {"entries": len(entries)}))
    runtime_policy = (root / "requirements-runtime.txt").read_text(encoding="utf-8") if (root / "requirements-runtime.txt").exists() else ""
    if "optional feature dependencies are declared in pyproject.toml extras" in runtime_policy.lower():
        checks.append(DoctorCheck("requirements-runtime.txt:policy", "ok", "blocking", "runtime dependency policy is explicit"))
    else:
        checks.append(DoctorCheck("requirements-runtime.txt:policy", "error", "blocking", "runtime dependency policy missing"))
    return checks


def _check_readme(root: Path) -> list[DoctorCheck]:
    path = root / "README.md"
    if not path.exists():
        return [DoctorCheck("README.md", "error", "blocking", "README.md missing")]
    content = path.read_text(encoding="utf-8")
    checks: list[DoctorCheck] = [DoctorCheck("README.md:present", "ok", "documentation", "README is present")]
    if "v18" in content:
        checks.append(DoctorCheck("README.md:current-runtime", "ok", "documentation", "README exposes current runtime version"))
    else:
        checks.append(DoctorCheck("README.md:current-runtime", "warning", "documentation", "README does not expose current runtime version"))
    if "python launcher.py health" in content:
        checks.append(DoctorCheck("README.md:health-command", "ok", "documentation", "health command documented"))
    else:
        checks.append(DoctorCheck("README.md:health-command", "warning", "documentation", "health command not documented"))
    if "CHANGELOG_*.md" in content:
        checks.append(DoctorCheck("README.md:deleted-changelog-reference", "error", "blocking", "README references deleted CHANGELOG_*.md source of truth"))
    else:
        checks.append(DoctorCheck("README.md:deleted-changelog-reference", "ok", "blocking", "README does not reference deleted CHANGELOG_*.md files"))
    if "pip install -e \".[dev]\"" in content:
        checks.append(DoctorCheck("README.md:editable-install", "ok", "documentation", "editable install documented"))
    else:
        checks.append(DoctorCheck("README.md:editable-install", "warning", "documentation", "editable install not documented"))
    return checks


def _check_forbidden_artifacts(root: Path) -> list[DoctorCheck]:
    findings: list[str] = []
    for path in root.rglob("*"):
        if any(part in IGNORED_ARTIFACT_PARTS for part in path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        if path.is_file() and path.parent == root and path.name.startswith(FORBIDDEN_ROOT_PREFIXES):
            findings.append(rel)
        if any(part in FORBIDDEN_CACHE_PARTS for part in path.parts):
            findings.append(rel)
        if path.is_file() and path.suffix in FORBIDDEN_FILE_SUFFIXES:
            findings.append(rel)
    if findings:
        return [DoctorCheck("repo:forbidden-artifacts", "error", "blocking", "forbidden cache/log/pid/obsolete artifacts found", {"files": sorted(set(findings))[:200], "count": len(set(findings))})]
    return [DoctorCheck("repo:forbidden-artifacts", "ok", "blocking", "no forbidden cache/log/pid/obsolete artifacts found")]


def _run_command(root: Path, args: tuple[str, ...], timeout_seconds: int) -> DoctorCheck:
    cmd = [sys.executable, "launcher.py", *args]
    try:
        result = subprocess.run(
            cmd,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return DoctorCheck("launcher:" + " ".join(args), "error", "blocking", "launcher command timed out", {"timeout_seconds": timeout_seconds})
    except Exception as exc:  # pragma: no cover - defensive runtime boundary
        return DoctorCheck("launcher:" + " ".join(args), "error", "blocking", "launcher command failed before execution", {"error": str(exc)})

    details = {
        "returncode": result.returncode,
        "stdout_prefix": result.stdout[:500],
        "stderr_prefix": result.stderr[:500],
    }
    if result.returncode == 0:
        return DoctorCheck("launcher:" + " ".join(args), "ok", "blocking", "launcher command returned zero", details)
    return DoctorCheck("launcher:" + " ".join(args), "error", "blocking", "launcher command returned non-zero", details)


def run_repo_doctor(
    project_root: str | Path,
    *,
    execute_runtime_checks: bool = False,
    timeout_seconds: int = 15,
    write_report: bool = False,
) -> RepoDoctorReport:
    root = Path(project_root).resolve()
    checks: list[DoctorCheck] = []

    if not root.exists():
        checks.append(DoctorCheck("project-root", "error", "blocking", "project root does not exist", {"path": str(root)}))
    elif not root.is_dir():
        checks.append(DoctorCheck("project-root", "error", "blocking", "project root is not a directory", {"path": str(root)}))
    else:
        checks.append(DoctorCheck("project-root", "ok", "blocking", "project root exists", {"path": str(root)}))
        checks.extend(_check_required_paths(root))
        checks.extend(_check_pytest_ini(root))
        checks.extend(_check_pyproject(root))
        checks.extend(_check_requirements(root))
        checks.extend(_check_readme(root))
        checks.extend(_check_forbidden_artifacts(root))
        if execute_runtime_checks:
            for args in LIGHTWEIGHT_COMMANDS:
                checks.append(_run_command(root, args, timeout_seconds))
        else:
            checks.append(DoctorCheck("launcher:runtime-smoke", "skipped", "diagnostic", "runtime smoke skipped; pass --execute-runtime-checks to enable"))

    ok = not any(check.status == "error" and check.severity == "blocking" for check in checks)
    report = RepoDoctorReport(ok=ok, project_root=str(root), executed_runtime_checks=execute_runtime_checks, checks=checks)

    if write_report and root.exists() and root.is_dir():
        target = root / "release" / "repo_doctor_latest.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    return report
