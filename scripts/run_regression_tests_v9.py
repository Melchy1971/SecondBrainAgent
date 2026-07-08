from pathlib import Path
import py_compile
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

failed = []

# 1. Python syntax
for py in ROOT.rglob("*.py"):
    if "__pycache__" in py.parts:
        continue
    try:
        py_compile.compile(str(py), doraise=True)
    except Exception as exc:
        failed.append(f"compile {py}: {exc}")

# 2. Required scripts/files
required = [
    ROOT / "scripts" / "menu.py",
    ROOT / "scripts" / "run_v9_cycle.py",
    ROOT / "scripts" / "import_ai_exports.py",
    ROOT / "scripts" / "api_gateway_v9.py",
    ROOT / "scripts" / "release_gate_v9.py",
    ROOT / "scripts" / "check_paths_v9.py",
    ROOT / "mcp-server" / "server.py",
]

for p in required:
    if not p.exists():
        failed.append(f"missing {p}")

# 3. Path check, if available
path_check = ROOT / "scripts" / "check_paths_v9.py"
if path_check.exists():
    result = subprocess.run(
        [sys.executable, str(path_check)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        failed.append("check_paths_v9.py failed:\n" + result.stdout + result.stderr)

if failed:
    print("Regression Tests v9: FAIL")
    for item in failed[:80]:
        print("-", item)
    raise SystemExit(2)

print("Regression Tests v9: PASS")
