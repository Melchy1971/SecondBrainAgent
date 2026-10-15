"""Runtime-Architektur-Gate: statische AST-Pruefungen und fail-closed-Logik."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from secondbrain.release import jarvis_1_0_gate as aggregator
from secondbrain.release import runtime_architecture_gate as gate


def _project(tmp_path: Path, *, entry: str, modules: dict[str, str]) -> Path:
    (tmp_path / "SecondBrain" / "gui").mkdir(parents=True)
    (tmp_path / "SecondBrain" / "gui" / "launch.py").write_text(entry, encoding="utf-8")
    for rel, code in modules.items():
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(code, encoding="utf-8")
    return tmp_path


CANONICAL_ENTRY = "from secondbrain.jobs.runtime import start_job_runtime\nstart_job_runtime('.')\n"


@pytest.fixture
def fail_closed(monkeypatch):
    monkeypatch.setattr(gate, "_job_runtime_state", lambda env: "blocked")


def test_clean_architecture_passes(tmp_path: Path, fail_closed) -> None:
    root = _project(tmp_path, entry=CANONICAL_ENTRY, modules={
        "SecondBrain/importing/pipeline.py": "class ImportScheduler:\n    pass\nImportScheduler()\n",
    })
    report = gate.run_runtime_architecture_gate(root, env={}, write_report=False)
    assert report["status"] == gate.PASS, report["details"]
    for criterion in ("canonical_job_runtime", "no_jsonl_production_fallback", "no_parallel_production_subsystems"):
        assert aggregator._criterion_passes(criterion, report)


@pytest.mark.parametrize("entry", [
    "from secondbrain.jobs.runtime import start_job_runtime\n",          # importiert, nie gestartet
    "from secondbrain.other import start_job_runtime\nstart_job_runtime('.')\n",
])
def test_entry_without_canonical_start_fails(tmp_path: Path, fail_closed, entry: str) -> None:
    report = gate.run_runtime_architecture_gate(_project(tmp_path, entry=entry, modules={}), env={},
                                                write_report=False)
    assert report["assertions"]["canonical_job_runtime"] is False


@pytest.mark.parametrize("code", [
    "from x import ImportScheduler\nImportScheduler(root)\n",
    "import secondbrain.importing.pipeline as p\nscheduler = p.ImportScheduler(root)\n",
])
def test_secondary_scheduler_outside_definition_is_found(tmp_path: Path, fail_closed, code: str) -> None:
    root = _project(tmp_path, entry=CANONICAL_ENTRY, modules={"SecondBrain/feature/streaming.py": code})
    report = gate.run_runtime_architecture_gate(root, env={}, write_report=False)
    assert report["assertions"]["no_parallel_production_subsystems"] is False
    assert report["details"]["secondary_scheduler_instantiations"][0].startswith("SecondBrain/feature/streaming.py:")


def test_scheduler_in_tests_is_ignored(tmp_path: Path, fail_closed) -> None:
    root = _project(tmp_path, entry=CANONICAL_ENTRY,
                    modules={"SecondBrain/importing/tests/test_x.py": "ImportScheduler()\n"})
    assert gate.run_runtime_architecture_gate(root, env={}, write_report=False)["status"] == gate.PASS


def test_canonical_production_variable_must_fail_closed(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        gate,
        "_job_runtime_state",
        lambda env: "blocked" if env == {"SECOND_BRAIN_ENV": "production"} else "degraded",
    )
    report = gate.run_runtime_architecture_gate(_project(tmp_path, entry=CANONICAL_ENTRY, modules={}), env={},
                                                write_report=False)
    assert report["assertions"]["no_jsonl_production_fallback"] is True
    assert report["details"]["production_without_database_state"] == {
        "SECOND_BRAIN_ENV": "blocked"}


def test_job_runtime_state_is_live_and_fail_closed_for_its_own_variable() -> None:
    # Echte JobRuntime: Produktion ohne Datenbank muss blockieren.
    assert gate._job_runtime_state({"SECOND_BRAIN_ENV": "production"}) == "blocked"


def test_legacy_production_variable_is_absent_from_runtime_code() -> None:
    source_root = Path(gate.__file__).resolve().parents[1]
    offenders = [
        path.relative_to(source_root).as_posix()
        for path in source_root.rglob("*.py")
        if "SECONDBRAIN_ENV" in path.read_text(encoding="utf-8")
    ]
    assert offenders == [], f"legacy production variable found in: {offenders}"


def test_launcher_command_exists(monkeypatch, tmp_path, capsys) -> None:
    import launcher

    monkeypatch.setattr(gate, "run_runtime_architecture_gate", lambda *a, **k: {"status": gate.BLOCKED})
    assert launcher.main(["runtime-architecture-gate", "--project-root", str(tmp_path), "--no-write-report"]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == gate.BLOCKED
