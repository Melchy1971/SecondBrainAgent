"""Hermetic policy gates shared by GitHub Actions and local CI tests."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA_ACTION = re.compile(r"^[\w.-]+/[\w.-]+@[0-9a-f]{40}(?:\s+#.+)?$")
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)(?:api[_-]?key|secret|token|password)\s*[=:]\s*['\"]?([A-Za-z0-9_\-/+=]{20,})"),
)
SECRET_EXCLUDES = (
    "tests/", "/tests/", "sample_docs/", ".env.example",
    # These modules contain synthetic canaries used to prove runtime redaction.
    "SecondBrain/agent/review_approval_gate.py",
    "SecondBrain/agent/review_approval_release_gate.py",
)


class GateError(RuntimeError):
    pass


def project_version(root: Path = ROOT) -> str:
    return str(tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"])


def check_version_drift(root: Path = ROOT) -> None:
    subprocess.run([sys.executable, "launcher.py", "version-sync"], cwd=root, check=True)
    result = subprocess.run(
        ["git", "diff", "--exit-code", "--", "README.md", "docs/09_MASTERPLAN_STATUS.json"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise GateError("version_drift: run `python launcher.py version-sync` and commit the result")


def check_tag(tag: str, root: Path = ROOT) -> None:
    expected = f"v{project_version(root)}"
    if tag != expected:
        raise GateError(f"tag_version_mismatch: expected {expected}, got {tag}")


def check_secrets(root: Path = ROOT) -> None:
    tracked = subprocess.run(
        ["git", "-c", f"safe.directory={root.resolve()}", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout.split(b"\0")
    findings: list[str] = []
    for raw in tracked:
        if not raw:
            continue
        relative = raw.decode("utf-8", errors="replace").replace("\\", "/")
        if any(marker in relative for marker in SECRET_EXCLUDES):
            continue
        path = root / relative
        if not path.is_file() or path.stat().st_size > 5_000_000:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            findings.append(relative)
    if findings:
        raise GateError("potential_secrets: " + ", ".join(sorted(findings)))


def check_workflows(root: Path = ROOT) -> None:
    issues: list[str] = []
    for path in sorted((root / ".github" / "workflows").glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        if not re.search(r"(?m)^permissions:\s*\n\s+contents:\s+read\s*$", text):
            issues.append(f"{path.name}: missing default contents: read")
        if "persist-credentials: false" not in text and "actions/checkout" in text:
            issues.append(f"{path.name}: checkout persists credentials")
        for match in re.finditer(r"(?m)^\s*uses:\s*([^\n]+)$", text):
            value = match.group(1).strip()
            if value.startswith("./"):
                continue
            if not SHA_ACTION.fullmatch(value):
                issues.append(f"{path.name}: unpinned action {value}")
    if issues:
        raise GateError("; ".join(issues))


def changed_python_files(base: str, root: Path = ROOT) -> list[str]:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={root.resolve()}", "diff", "--name-only", "-z", f"{base}...HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    allowed_roots = ("SecondBrain/", "scripts/", "tests/")
    paths = result.stdout.decode("utf-8", errors="strict").split("\0")
    return sorted(
        path
        for path in paths
        if path.endswith(".py")
        and path.startswith(allowed_roots)
        and (root / path).is_file()
    )


def check_changed_python(base: str, root: Path = ROOT) -> None:
    paths = changed_python_files(base, root)
    if paths:
        subprocess.run([sys.executable, "-m", "ruff", "check", *paths], cwd=root, check=True)


def check_changed_installer_types(base: str, root: Path = ROOT) -> None:
    installer_roots = ("SecondBrain/install/", "SecondBrain/installer_update/")
    paths = [path for path in changed_python_files(base, root) if path.startswith(installer_roots)]
    if paths:
        subprocess.run(
            [sys.executable, "-m", "mypy", "--ignore-missing-imports", *paths],
            cwd=root,
            check=True,
        )


def check_changed_tests(base: str, root: Path = ROOT) -> None:
    paths = [path for path in changed_python_files(base, root) if path.startswith("tests/")]
    if paths:
        subprocess.run([sys.executable, "-m", "pytest", "-q", *paths], cwd=root, check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "gate",
        choices=("version", "tag", "secrets", "workflows", "lint-diff", "type-diff", "test-diff"),
    )
    parser.add_argument("--tag", default="")
    parser.add_argument("--base", default="")
    args = parser.parse_args(argv)
    try:
        {
            "version": check_version_drift,
            "tag": lambda: check_tag(args.tag),
            "secrets": check_secrets,
            "workflows": check_workflows,
            "lint-diff": lambda: check_changed_python(args.base),
            "type-diff": lambda: check_changed_installer_types(args.base),
            "test-diff": lambda: check_changed_tests(args.base),
        }[args.gate]()
    except (GateError, subprocess.CalledProcessError) as exc:
        print(f"CI gate failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
