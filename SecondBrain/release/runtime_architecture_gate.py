"""Runtime-Architektur-Gate: eine kanonische Job-Runtime, kein JSONL in Produktion.

Kriterien (vom jarvis-1.0-gate geprueft):

``canonical_job_runtime``
    Der produktive Einstiegspunkt (``secondbrain.gui.launch``) startet die Job-
    Runtime ueber ``secondbrain.jobs.runtime.start_job_runtime`` -- statisch per
    AST geprueft.
``no_jsonl_production_fallback``
    Live: Eine ``JobRuntime`` in Produktion ohne Datenbank ist ``blocked``
    (fail-closed), nie ``degraded``/JSONL -- fuer jede im Projekt verwendete
    Schreibweise der Produktionsvariable (``SECONDBRAIN_ENV`` der Job-Runtime,
    ``SECOND_BRAIN_ENV`` der Datenbank-Policy).
``no_parallel_production_subsystems``
    Kein Modul ausserhalb des eigenen Definitionsmoduls instanziiert einen
    zweiten Job-Scheduler (``SECONDARY_SCHEDULERS``) -- statisch per AST.
"""

from __future__ import annotations

import ast
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

from secondbrain.release.evidence import seal

PASS, BLOCKED = "PASS", "BLOCKED"
SCHEMA = "secondbrain.runtime_architecture_gate.v1"
REPORT_PATH = Path("runtime/reports/runtime_architecture_gate.json")

ENTRY_MODULE = Path("SecondBrain/gui/launch.py")
CANONICAL_MODULE = "secondbrain.jobs.runtime"
CANONICAL_START = "start_job_runtime"
# Bekannte Scheduler neben der kanonischen Job-Runtime -> Definitionsmodul.
SECONDARY_SCHEDULERS = {"ImportScheduler": "SecondBrain/importing/pipeline.py"}
PRODUCTION_VARIABLES = ("SECONDBRAIN_ENV", "SECOND_BRAIN_ENV")


def _canonical_job_runtime(root: Path) -> tuple[bool, str]:
    path = root / ENTRY_MODULE
    if not path.is_file():
        return False, "entry module missing"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported = any(
        isinstance(node, ast.ImportFrom) and node.module == CANONICAL_MODULE
        and any(alias.name == CANONICAL_START for alias in node.names)
        for node in ast.walk(tree)
    )
    called = any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == CANONICAL_START
        for node in ast.walk(tree)
    )
    return imported and called, f"imports={imported}, calls={called}"


def _job_runtime_state(env: Mapping[str, str]) -> str:
    from secondbrain.jobs.runtime import JobRuntime

    with tempfile.TemporaryDirectory() as temp:  # Worker-ID nicht im Projekt ablegen
        return str(JobRuntime(temp, env=dict(env)).start().get("state"))


def _no_jsonl_production_fallback() -> tuple[bool, dict[str, str]]:
    states = {}
    for variable in PRODUCTION_VARIABLES:
        # Nur diese eine Variable gesetzt, keine Datenbank: muss fail-closed sein.
        states[variable] = _job_runtime_state({variable: "production"})
    return all(state == "blocked" for state in states.values()), states


def _scheduler_instantiations(root: Path) -> list[str]:
    findings: list[str] = []
    package = root / "SecondBrain"
    for path in sorted(package.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        if "/tests/" in f"/{rel}" or rel.endswith("_test.py"):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            findings.append(f"{rel}:unparseable")
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.id if isinstance(node.func, ast.Name) else (
                node.func.attr if isinstance(node.func, ast.Attribute) else None)
            if name in SECONDARY_SCHEDULERS and rel != SECONDARY_SCHEDULERS[name]:
                findings.append(f"{rel}:{node.lineno}:{name}")
    return findings


def run_runtime_architecture_gate(
    project_root: str | Path = ".",
    *,
    env: Mapping[str, str] | None = None,
    write_report: bool = True,
) -> dict[str, Any]:
    values = dict(os.environ if env is None else env)
    root = Path(project_root).resolve()
    canonical, canonical_detail = _canonical_job_runtime(root)
    fail_closed, states = _no_jsonl_production_fallback()
    parallel = _scheduler_instantiations(root)
    assertions = {
        "canonical_job_runtime": canonical,
        "no_jsonl_production_fallback": fail_closed,
        "no_parallel_production_subsystems": not parallel,
    }
    status = PASS if all(assertions.values()) else BLOCKED
    report = seal({
        "status": status, "ok": status == PASS, "assertions": assertions,
        "details": {
            "canonical_job_runtime": canonical_detail,
            "production_without_database_state": states,
            "secondary_scheduler_instantiations": parallel,
        },
    }, schema=SCHEMA, root=root, env=values)
    if write_report:
        target = root / REPORT_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        report = {**report, "report": REPORT_PATH.as_posix()}
    return report
