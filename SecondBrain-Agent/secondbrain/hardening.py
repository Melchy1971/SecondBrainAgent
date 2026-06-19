from pathlib import Path
import sys
import json
from .utils import now_date, now_datetime
from .config import load_settings, load_simple_yaml

REQUIRED_DIRS = [
    "00_Inbox",
    "01_Projekte",
    "02_Wissen",
    "04_Tasks",
    "05_Quellen",
    "06_Journal",
    "07_Graph",
    "90_Templates",
    "99_System",
]

def validate_paths(settings: dict, project_root: Path) -> list[tuple[str, bool, str]]:
    vault = Path(settings.get("vault_path", ""))
    inbox = Path(settings.get("inbox_path", ""))
    checks = [
        ("python_version", sys.version_info >= (3, 10), f"{sys.version_info.major}.{sys.version_info.minor}"),
        ("project_root_exists", project_root.exists(), str(project_root)),
        ("vault_exists", vault.exists(), str(vault)),
        ("inbox_exists", inbox.exists(), str(inbox)),
        ("config_exists", (project_root / "config").exists(), str(project_root / "config")),
        ("scripts_exists", (project_root / "scripts").exists(), str(project_root / "scripts")),
        ("secondbrain_package_exists", (project_root / "secondbrain").exists(), str(project_root / "secondbrain")),
    ]

    for d in REQUIRED_DIRS:
        checks.append((f"vault_dir_{d}", (vault / d).exists(), str(vault / d)))

    return checks

def write_runtime_diagnostics(project_root: Path) -> Path:
    settings = load_settings(project_root)
    vault = Path(settings.get("vault_path", project_root))
    target_dir = vault / "99_System" / "runtime_diagnostics"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{now_date()}_runtime-diagnostics.md"

    checks = validate_paths(settings, project_root)
    lines = [
        f"# Runtime Diagnostics {now_datetime()}",
        "",
        "| Check | Status | Details |",
        "|---|---|---|"
    ]
    for name, ok, detail in checks:
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | `{detail}` |")

    target.write_text("\n".join(lines), encoding="utf-8")
    return target

def hardening_score(project_root: Path) -> dict:
    settings = load_settings(project_root)
    checks = validate_paths(settings, project_root)
    passed = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0
    return {
        "score": score,
        "passed": passed,
        "total": total,
        "checks": checks,
    }
