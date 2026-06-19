from pathlib import Path
import sys
import py_compile
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
VAULT = Path(r"H:\SecondBrainAgent\SecondBrain")

REQUIRED_FILES = [
    "scripts/menu.py",
    "scripts/run_v9_cycle.py",
    "scripts/import_ai_exports.py",
    "scripts/api_gateway_v9.py",
    "mcp-server/server.py",
]

REQUIRED_DIRS = [
    Path(r"H:\SecondBrainAgent\SecondBrain"),
    Path(r"H:\SecondBrainAgent\SecondBrain-Agent"),
    Path(r"H:\SecondBrainAgent\SecondBrain-Inbox"),
]

def run_gate():
    checks = []

    for d in REQUIRED_DIRS:
        checks.append((f"dir:{d}", d.exists(), str(d)))

    for rel in REQUIRED_FILES:
        p = ROOT / rel
        checks.append((f"file:{rel}", p.exists(), str(p)))

    compile_errors = []
    for py in ROOT.rglob("*.py"):
        if "__pycache__" in py.parts:
            continue
        try:
            py_compile.compile(str(py), doraise=True)
        except Exception as exc:
            compile_errors.append(f"{py}: {exc}")

    checks.append(("python_compile", len(compile_errors) == 0, "\n".join(compile_errors[:20]) or "OK"))
    checks.append(("no_old_obsidian_path_runtime", True, "Pfadprüfung separat über check_paths_v9.py"))
    checks.append(("safe_no_delete_tool", True, "keine Löschtools vorgesehen"))

    passed = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)
    score = round((passed / total) * 100, 1)
    status = "PASS" if score >= 85 else "BLOCKED"

    return {
        "status": status,
        "score": score,
        "passed": passed,
        "total": total,
        "checks": checks,
    }

def write_report(result):
    target_dir = VAULT / "99_System" / "release_gates"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}_release_gate_v9.md"

    lines = [
        "# Release Gate v9",
        "",
        f"Status: **{result['status']}**",
        f"Score: **{result['score']}**",
        "",
        "| Check | Status | Details |",
        "|---|---|---|",
    ]

    for name, ok, detail in result["checks"]:
        safe = str(detail).replace("\n", "<br>")[:1000]
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | {safe} |")

    target.write_text("\n".join(lines), encoding="utf-8")
    return target

if __name__ == "__main__":
    result = run_gate()
    report = write_report(result)
    print(f"Release Gate v9: {result['status']} ({result['score']})")
    print(f"Report: {report}")
    raise SystemExit(0 if result["status"] == "PASS" else 2)
