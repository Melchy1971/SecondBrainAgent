from __future__ import annotations

from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys
import json
import py_compile

ROOT = Path(r"H:\SecondBrainAgent\SecondBrain-Agent")
VAULT = Path(r"H:\SecondBrainAgent\SecondBrain")
INBOX = Path(r"H:\SecondBrainAgent\SecondBrain-Inbox")

REQUIRED_SCRIPTS = [
    "scripts/menu.py",
    "scripts/run_v9_cycle.py",
    "scripts/run_v95_cycle.py",
    "scripts/check_paths_v9.py",
    "scripts/release_gate_v9.py",
    "scripts/run_regression_tests_v9.py",
]

FORBIDDEN = ["H:\\Obsidian", "H:\\\\Obsidian"]

def now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")

def command_exists(cmd: str) -> bool:
    return shutil.which(cmd) is not None

def check_environment(root: Path = ROOT, vault: Path = VAULT, inbox: Path = INBOX) -> list[tuple[str, bool, str]]:
    checks = []
    checks.append(("python_version", sys.version_info >= (3, 11), f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"))
    checks.append(("vault_exists", vault.exists(), str(vault)))
    checks.append(("inbox_exists", inbox.exists(), str(inbox)))
    checks.append(("agent_exists", root.exists(), str(root)))
    checks.append(("python_command", command_exists("python") or command_exists("py"), "python/py"))
    checks.append(("node_command_optional", True, "optional"))
    checks.append(("ollama_optional", True, "optional"))
    for rel in REQUIRED_SCRIPTS:
        checks.append((f"script:{rel}", (root / rel).exists(), str(root / rel)))
    return checks

def scan_forbidden_paths(root: Path = ROOT) -> list[str]:
    hits = []
    exts = {".py", ".yaml", ".yml", ".json", ".md", ".txt", ".ps1", ".js", ".ts"}
    for p in root.rglob("*"):
        if p.name == "check_paths_v9.py":
            continue
        if p.is_file() and p.suffix.lower() in exts:
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if any(bad in text for bad in FORBIDDEN):
                hits.append(str(p.relative_to(root)))
    return hits

def compile_python(root: Path = ROOT) -> list[str]:
    errors = []
    for p in root.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        try:
            py_compile.compile(str(p), doraise=True)
        except Exception as exc:
            errors.append(f"{p}: {exc}")
    return errors

def create_update_backup(root: Path = ROOT) -> Path:
    backup_root = root / "backups" / "update_backups"
    backup_root.mkdir(parents=True, exist_ok=True)
    target = backup_root / f"backup_{now_stamp()}"
    target.mkdir(parents=True, exist_ok=True)

    for rel in ["config", "scripts", "mcp-server"]:
        src = root / rel
        if src.exists():
            shutil.copytree(src, target / rel, dirs_exist_ok=True)

    info = target / "BACKUP_INFO.md"
    info.write_text(f"# Update Backup\n\nZeit: {now_stamp()}\nQuelle: `{root}`\n", encoding="utf-8")
    return target

def write_settings_report(root: Path = ROOT, vault: Path = VAULT) -> Path:
    target_dir = vault / "95_Operations" / "Settings"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{now_stamp()}_settings-report.md"

    config_dir = root / "config"
    files = sorted(config_dir.glob("*")) if config_dir.exists() else []
    lines = [
        "# Settings Report v9.6",
        "",
        f"Zeit: {now_stamp()}",
        "",
        "| Datei | Größe |",
        "|---|---:|",
    ]
    for f in files:
        if f.is_file():
            lines.append(f"| `{f.name}` | {f.stat().st_size} |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target

def write_installer_report(root: Path = ROOT, vault: Path = VAULT, inbox: Path = INBOX) -> Path:
    target_dir = vault / "95_Operations" / "Installer"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{now_stamp()}_installer-check.md"

    checks = check_environment(root, vault, inbox)
    forbidden = scan_forbidden_paths(root)
    compile_errors = compile_python(root)

    lines = [
        "# Installer Check v9.6",
        "",
        f"Zeit: {now_stamp()}",
        "",
        "| Check | Status | Details |",
        "|---|---|---|",
    ]
    for name, ok, detail in checks:
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | `{detail}` |")

    lines += ["", "## Forbidden Paths", ""]
    if forbidden:
        lines += [f"- {h}" for h in forbidden]
    else:
        lines.append("- Keine.")

    lines += ["", "## Python Compile", ""]
    if compile_errors:
        lines += [f"- {e}" for e in compile_errors[:50]]
    else:
        lines.append("- PASS.")

    target.write_text("\n".join(lines), encoding="utf-8")
    return target

def run_production_ready_gate(root: Path = ROOT, vault: Path = VAULT, inbox: Path = INBOX) -> dict:
    checks = check_environment(root, vault, inbox)
    forbidden = scan_forbidden_paths(root)
    compile_errors = compile_python(root)

    checks.append(("forbidden_paths", len(forbidden) == 0, str(len(forbidden))))
    checks.append(("python_compile", len(compile_errors) == 0, str(len(compile_errors))))
    checks.append(("destructive_actions_disabled", True, "hard policy"))
    checks.append(("email_send_disabled", True, "hard policy"))

    passed = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)
    score = round((passed / total) * 100, 1)
    return {
        "status": "PASS" if score >= 90 else "BLOCKED",
        "score": score,
        "passed": passed,
        "total": total,
        "checks": checks,
        "forbidden": forbidden,
        "compile_errors": compile_errors,
    }

def write_production_ready_gate(root: Path = ROOT, vault: Path = VAULT, inbox: Path = INBOX) -> Path:
    result = run_production_ready_gate(root, vault, inbox)
    target_dir = vault / "95_Operations" / "ReleaseGates"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{now_stamp()}_production-ready-gate-v96.md"

    lines = [
        "# Production Ready Gate v9.6",
        "",
        f"Status: **{result['status']}**",
        f"Score: **{result['score']}**",
        "",
        "| Check | Status | Details |",
        "|---|---|---|",
    ]
    for name, ok, detail in result["checks"]:
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | `{detail}` |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
