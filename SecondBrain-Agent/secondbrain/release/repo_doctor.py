from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


REQUIRED_PATHS: tuple[str, ...] = (
    "launcher.py",
    "pytest.ini",
    "requirements.txt",
    "secondbrain/module_registry.py",
    "secondbrain/launcher_runtime_v126.py",
    "secondbrain/p0_runtime.py",
    "secondbrain/p1_rag_runtime.py",
)

EXPECTED_PYTEST_LINES: tuple[str, ...] = (
    "testpaths = tests",
    "pythonpath = .",
)

LIGHTWEIGHT_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("health",),
    ("command-index",),
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


def _check_requirements(root: Path) -> list[DoctorCheck]:
    path = root / "requirements.txt"
    if not path.exists():
        return [DoctorCheck("requirements.txt", "error", "blocking", "requirements.txt missing")]
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.strip().startswith("#")]
    checks = [DoctorCheck("requirements.txt:readable", "ok", "blocking", "requirements file readable", {"entries": len(lines)})]
    if len(lines) <= 1:
        checks.append(
            DoctorCheck(
                "requirements.txt:runtime-dependencies",
                "warning",
                "release-risk",
                "only minimal dependencies are declared; runtime reproducibility is weak",
                {"entries": lines},
            )
        )
    else:
        checks.append(DoctorCheck("requirements.txt:runtime-dependencies", "ok", "release-risk", "runtime dependency list is populated"))
    return checks


def _check_readme(root: Path) -> list[DoctorCheck]:
    path = root / "README.md"
    if not path.exists():
        return [DoctorCheck("README.md", "warning", "documentation", "README.md missing")]
    content = path.read_text(encoding="utf-8")
    checks: list[DoctorCheck] = [DoctorCheck("README.md:present", "ok", "documentation", "README is present")]
    if "v12.6" not in content and "v18" not in content:
        checks.append(DoctorCheck("README.md:current-runtime", "warning", "documentation", "README does not expose current runtime version"))
    if "python launcher.py health" in content:
        checks.append(DoctorCheck("README.md:health-command", "ok", "documentation", "health command documented"))
    else:
        checks.append(DoctorCheck("README.md:health-command", "warning", "documentation", "health command not documented"))
    return checks


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
        checks.extend(_check_requirements(root))
        checks.extend(_check_readme(root))
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
