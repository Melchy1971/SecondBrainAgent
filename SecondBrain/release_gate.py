from pathlib import Path
import subprocess
import sys
from .utils import now_date, now_datetime
from .config import load_settings, load_simple_yaml
from .hardening import hardening_score
from .governance import scan_secret_leaks

def _run_script(project_root: Path, script_name: str) -> tuple[bool, str]:
    script = project_root / "scripts" / script_name
    if not script.exists():
        return False, f"Script fehlt: {script_name}"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        timeout=120
    )
    output = (result.stdout + "\n" + result.stderr)[-3000:]
    return result.returncode == 0, output

def run_release_gate(project_root: Path) -> dict:
    settings = load_settings(project_root)
    production_cfg = load_simple_yaml(project_root / "config" / "production.yaml").get("production", {})
    threshold = int(production_cfg.get("release_gate_threshold", 85))

    hardening = hardening_score(project_root)
    secrets = scan_secret_leaks(settings)

    smoke_ok, smoke_output = _run_script(project_root, "run_tests.py") if (project_root / "scripts" / "run_tests.py").exists() else (False, "run_tests.py fehlt")
    backup_ok, backup_output = _run_script(project_root, "backup_restore_test.py") if (project_root / "scripts" / "backup_restore_test.py").exists() else (False, "backup_restore_test.py fehlt")

    checks = [
        ("hardening_score", hardening["score"] >= threshold, f"{hardening['score']} / {threshold}"),
        ("secret_scan", len(secrets) == 0, f"{len(secrets)} Findings"),
        ("smoke_tests", smoke_ok, smoke_output),
        ("backup_restore_test", backup_ok, backup_output),
        ("destructive_actions_disabled", not settings.get("destructive_actions_allowed", False), "destructive_actions_allowed=false"),
        ("email_send_disabled", not settings.get("email_send_allowed", False), "email_send_allowed=false"),
    ]

    passed = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)
    score = round((passed / total) * 100, 1)
    status = "PASS" if score >= threshold else "BLOCKED"

    return {
        "status": status,
        "score": score,
        "threshold": threshold,
        "checks": checks,
        "hardening": hardening,
        "secret_findings": secrets,
    }

def write_release_gate_report(project_root: Path) -> Path:
    settings = load_settings(project_root)
    vault = Path(settings["vault_path"])
    target_dir = vault / "99_System" / "release_gates"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{now_date()}_release-gate-v6-1.md"

    result = run_release_gate(project_root)

    lines = [
        f"# Release Gate v6.1 {now_datetime()}",
        "",
        f"Status: **{result['status']}**",
        f"Score: **{result['score']} / 100**",
        f"Threshold: **{result['threshold']}**",
        "",
        "| Check | Status | Details |",
        "|---|---|---|",
    ]

    for name, ok, detail in result["checks"]:
        safe = str(detail).replace("\n", "<br>")[:1000]
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | {safe} |")

    lines += [
        "",
        "## Hardening Details",
        "",
        "| Check | Status | Details |",
        "|---|---|---|",
    ]
    for name, ok, detail in result["hardening"]["checks"]:
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | `{detail}` |")

    lines += ["", "## Secret Findings", ""]
    if not result["secret_findings"]:
        lines.append("- Keine.")
    else:
        for f in result["secret_findings"]:
            lines.append(f"- `{f['file']}`")

    target.write_text("\n".join(lines), encoding="utf-8")
    return target
