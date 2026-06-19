from pathlib import Path
import subprocess
import sys
from .v9_common import now_date, now_dt, ensure

def run_script(agent_root: Path, script: str, *args: str) -> tuple[bool, str]:
    p = agent_root / "scripts" / script
    if not p.exists():
        return False, f"Script fehlt: {script}"
    result = subprocess.run([sys.executable, str(p), *args], cwd=str(agent_root), capture_output=True, text=True)
    return result.returncode == 0, (result.stdout + "\n" + result.stderr)[-4000:]

def run_workflow(agent_root: Path, vault: Path, workflow: str) -> Path:
    folder = ensure(vault / "76_WorkflowEngine")
    target = folder / f"{now_date()}_workflow_{workflow}.md"
    steps = []

    if workflow == "import_all":
        steps = ["import_ai_exports.py", "run_secondbrain_os_cycle.py"]
    elif workflow == "daily_briefing":
        steps = ["run_secondbrain_os_cycle.py"]
    elif workflow == "weekly_review":
        steps = ["run_secondbrain_os_cycle.py"]
    else:
        steps = ["run_secondbrain_os_cycle.py"]

    lines = [f"# Workflow: {workflow}", "", f"Zeit: {now_dt()}", "", "| Step | Status | Output |", "|---|---|---|"]
    for s in steps:
        ok, out = run_script(agent_root, s)
        lines.append(f"| {s} | {'PASS' if ok else 'WARN'} | {out.replace(chr(10), '<br>')[:1000]} |")

    target.write_text("\n".join(lines), encoding="utf-8")
    return target

def write_workflow_catalog(vault: Path) -> Path:
    folder = ensure(vault / "76_WorkflowEngine")
    target = folder / "Workflow_Catalog.md"
    lines = [
        "# Workflow Catalog",
        "",
        "| Workflow | Zweck |",
        "|---|---|",
        "| import_all | ChatGPT, Gemini, Perplexity importieren und OS aktualisieren |",
        "| daily_briefing | Tageslage, Projekte, Risiken, Empfehlungen |",
        "| weekly_review | Wochenreview, Lernen, Digital Twin |",
        "| project_plan | Projektordner und Projektintelligenz |",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
