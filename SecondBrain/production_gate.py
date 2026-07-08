from pathlib import Path
import sys
import subprocess
from .utils import now_date, now_datetime
from .config import load_settings
from .validator import validate_environment
from .quality import quality_gate
from .governance import scan_secret_leaks

def run_production_gate(project_root: Path) -> dict:
    settings = load_settings(project_root)
    validation = validate_environment(settings, project_root)
    q_ok, q_issues = quality_gate(settings)
    secrets = scan_secret_leaks(settings)

    checks = []
    checks.append(("environment", validation["ok"], "Pfad- und Python-Prüfung"))
    checks.append(("quality_gate", q_ok, "; ".join(q_issues) if q_issues else "OK"))
    checks.append(("secret_scan", len(secrets) == 0, f"{len(secrets)} Findings"))

    score = 0
    for _, ok, _ in checks:
        score += 100 / len(checks) if ok else 0

    return {
        "score": round(score, 1),
        "status": "PASS" if score >= 85 else "BLOCKED",
        "checks": checks,
        "secret_findings": secrets,
    }

def write_production_gate_report(project_root: Path) -> Path:
    settings = load_settings(project_root)
    vault = Path(settings["vault_path"])
    target_dir = vault / "99_System" / "production"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{now_date()}_production-gate.md"
    result = run_production_gate(project_root)

    lines = [
        f"# Production Gate {now_datetime()}",
        "",
        f"Status: **{result['status']}**",
        f"Score: **{result['score']}**",
        "",
        "| Check | Status | Hinweis |",
        "|---|---|---|",
    ]
    for name, ok, hint in result["checks"]:
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | {hint} |")
    lines += ["", "## Secret Findings", ""]
    if not result["secret_findings"]:
        lines.append("- Keine.")
    else:
        for f in result["secret_findings"]:
            lines.append(f"- `{f['file']}`")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
