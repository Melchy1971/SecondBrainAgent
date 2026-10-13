"""Commit-gebundener Umschlag: Versiegelung, Umgebung, Abgleich mit dem Aggregator."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from secondbrain.release import evidence
from secondbrain.release import jarvis_1_0_gate as gate

NOW = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)


def _repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for key, value in (("user.email", "gate@example.invalid"), ("user.name", "Gate")):
        subprocess.run(["git", "-C", str(tmp_path), "config", key, value], check=True)
    (tmp_path / "code.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "code.py"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-q", "-m", "init"], check=True)
    return tmp_path


def test_seal_binds_commit_environment_and_validity(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    sealed = evidence.seal({"status": "PASS"}, schema="secondbrain.x.v1", root=root, env={}, now=NOW)
    assert sealed["schema"] == "secondbrain.x.v1"
    assert sealed["commit_sha"] == evidence.git_commit(root) and len(sealed["commit_sha"]) == 40
    assert sealed["worktree_clean"] is True
    assert sealed["environment"] == "local"
    assert sealed["generated_at"] == NOW.isoformat()
    assert sealed["expires_at"] == (NOW + timedelta(hours=24)).isoformat()
    assert sealed["evidence_sha256"] == evidence.canonical_hash(sealed)


def test_seal_detects_uncommitted_changes(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "code.py").write_text("x = 2\n", encoding="utf-8")
    assert evidence.seal({}, schema="s", root=root, env={})["worktree_clean"] is False


def test_seal_keeps_existing_timezone_aware_generated_at(tmp_path: Path) -> None:
    earlier = (NOW - timedelta(hours=2)).isoformat()
    sealed = evidence.seal({"generated_at": earlier}, schema="s", root=_repo(tmp_path), env={}, now=NOW)
    assert sealed["generated_at"] == earlier
    assert sealed["expires_at"] == (NOW + timedelta(hours=22)).isoformat()


def test_seal_rejects_foreign_schema_and_unknown_environment(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    with pytest.raises(ValueError, match="schema mismatch"):
        evidence.seal({"schema": "other.v1"}, schema="s.v1", root=root)
    with pytest.raises(ValueError, match="unknown evidence environment"):
        evidence.seal({}, schema="s", root=root, environment="prod")


@pytest.mark.parametrize("env,expected", [
    ({}, "local"),
    ({"GITHUB_ACTIONS": "true"}, "ci"),
    ({"SECONDBRAIN_EVIDENCE_ENVIRONMENT": "production"}, "production"),
    ({"SECONDBRAIN_EVIDENCE_ENVIRONMENT": "Clean-Windows", "GITHUB_ACTIONS": "true"}, "clean-windows"),
])
def test_environment_is_never_guessed_as_production(env: dict, expected: str) -> None:
    assert evidence.evidence_environment(env) == expected


def test_invalid_environment_value_is_rejected() -> None:
    with pytest.raises(ValueError):
        evidence.evidence_environment({"SECONDBRAIN_EVIDENCE_ENVIRONMENT": "prod"})


def test_sealed_evidence_passes_aggregator_integrity_and_commit_checks(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    spec = gate.EvidenceSpec("demo-gate", "runtime/reports/demo.json", "secondbrain.demo.v1", "local", ())
    sealed = evidence.seal({"status": "PASS"}, schema=spec.schema, root=root, env={})
    target = root / spec.path
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(sealed), encoding="utf-8")
    report = gate.run_jarvis_1_0_gate(root, specs=(spec,), write_report=False, update_masterplan=False)
    assert report["status"] == gate.PASS, report["blockers"]


def test_aggregator_blocks_evidence_from_dirty_worktree(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "code.py").write_text("x = 3\n", encoding="utf-8")
    spec = gate.EvidenceSpec("demo-gate", "runtime/reports/demo.json", "secondbrain.demo.v1", "local", ())
    sealed = evidence.seal({"status": "PASS"}, schema=spec.schema, root=root, env={})
    (root / "runtime" / "reports").mkdir(parents=True)
    (root / spec.path).write_text(json.dumps(sealed), encoding="utf-8")
    report = gate.run_jarvis_1_0_gate(root, specs=(spec,), write_report=False, update_masterplan=False)
    assert {b["cause"] for b in report["blockers"]} == {"dirty_worktree"}
