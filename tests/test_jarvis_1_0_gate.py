"""Strict positive and negative contracts for the Jarvis 1.0 gate."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from secondbrain.release import jarvis_1_0_gate as gate

NOW = datetime(2026, 7, 23, 10, 0, tzinfo=timezone.utc)
COMMIT = "a" * 40


def _payload(spec: gate.EvidenceSpec, *, status: str = gate.PASS) -> dict:
    report = {
        "schema": spec.schema,
        "generated_at": (NOW - timedelta(minutes=5)).isoformat(),
        "expires_at": (NOW + timedelta(hours=1)).isoformat(),
        "commit_sha": COMMIT,
        "environment": spec.environment,
        "status": status,
    }
    if spec.gate == "postgres-live-gate":
        report.update({
            "tls": {"active": True, "sslmode": "verify-full", "hostname_verified": True},
            "facts": {
                "repository_contracts": {"status": gate.PASS},
                "workspace_isolation": {"status": gate.PASS},
            },
        })
    elif spec.gate == "connector-e2e-gate":
        report.update({
            "release_scope_connectors": ["gmail", "calendar"],
            "connectors": [
                {"name": "gmail", "status": gate.PASS},
                {"name": "calendar", "status": gate.PASS},
            ],
        })
    elif spec.gate == "runtime-architecture-gate":
        report["assertions"] = {
            "canonical_job_runtime": True,
            "no_jsonl_production_fallback": True,
            "no_parallel_production_subsystems": True,
        }
    elif spec.gate == "native-voice-app-gate":
        report["components"] = {"desktop": gate.PASS, "voice": gate.PASS}
    elif spec.gate == "os-keyring-gate":
        report.update({"backend": "os_keyring", "secure_backend": True})
    elif spec.gate == "windows-installer-gate":
        report["signature_status"] = gate.PASS
    elif spec.gate == "full-test-suite":
        report.update({"complete": True, "failed": 0, "errors": 0})
    elif spec.gate == "version-sync-gate":
        report.update({
            "synchronized": True,
            "masterplan_version": "31.94.0",
            "package_version": "31.94.0",
        })
    elif spec.gate == "ci-commit-gate":
        report["conclusion"] = "success"
    if spec.required_phases:
        report["phases"] = [
            {"name": name, "status": gate.PASS} for name in spec.required_phases
        ]
    return gate.seal_evidence(report)


def _write(root: Path, spec: gate.EvidenceSpec, report: dict | None = None) -> Path:
    target = root / spec.path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report or _payload(spec)), encoding="utf-8")
    return target


def _write_all(root: Path) -> None:
    for spec in gate.EVIDENCE_SPECS:
        _write(root, spec)


def _run(root: Path, **kwargs):
    return gate.run_jarvis_1_0_gate(
        root, commit_sha=COMMIT, now=NOW, write_report=False,
        update_masterplan=False, **kwargs,
    )


def test_complete_valid_evidence_is_deterministic_pass(tmp_path: Path) -> None:
    _write_all(tmp_path)
    first = _run(tmp_path)
    second = _run(tmp_path)
    assert first["status"] == gate.PASS
    assert first["gate_matrix"] == second["gate_matrix"]
    assert not first["blockers"] and not first["failures"]
    assert all(row["status"] == gate.PASS for row in first["gate_matrix"])


def test_missing_reports_are_individual_blockers(tmp_path: Path) -> None:
    report = _run(tmp_path)
    assert report["status"] == gate.BLOCKED
    assert len(report["blockers"]) == len(gate.EVIDENCE_SPECS)
    assert all(
        set(row) == {"gate", "cause", "required_evidence"}
        and row["cause"] == "missing_report"
        for row in report["blockers"]
    )


def test_stale_report_is_rejected(tmp_path: Path) -> None:
    _write_all(tmp_path)
    spec = gate.EVIDENCE_SPECS[0]
    report = _payload(spec)
    report["generated_at"] = (NOW - timedelta(days=2)).isoformat()
    _write(tmp_path, spec, gate.seal_evidence(report))
    result = _run(tmp_path)
    assert result["status"] == gate.BLOCKED
    assert any(row["cause"] == "stale_report" for row in result["blockers"])


def test_tampered_report_is_rejected(tmp_path: Path) -> None:
    _write_all(tmp_path)
    spec = gate.EVIDENCE_SPECS[2]
    report = _payload(spec)
    report["status"] = gate.FAIL  # hash intentionally not refreshed
    _write(tmp_path, spec, report)
    result = _run(tmp_path)
    assert any(row["cause"] == "integrity_hash_mismatch" for row in result["blockers"])


def test_report_from_other_commit_is_rejected(tmp_path: Path) -> None:
    _write_all(tmp_path)
    spec = gate.EVIDENCE_SPECS[3]
    report = _payload(spec)
    report["commit_sha"] = "b" * 40
    _write(tmp_path, spec, gate.seal_evidence(report))
    assert any(row["cause"] == "commit_mismatch" for row in _run(tmp_path)["blockers"])


@pytest.mark.parametrize("source_status", [gate.SKIPPED, gate.CONDITIONAL_PASS])
def test_mandatory_non_pass_status_fails(tmp_path: Path, source_status: str) -> None:
    _write_all(tmp_path)
    spec = gate.EVIDENCE_SPECS[1]
    _write(tmp_path, spec, _payload(spec, status=source_status))
    result = _run(tmp_path)
    assert result["status"] == gate.FAIL
    assert any(source_status.lower() in row["cause"] for row in result["failures"])


def test_contradictory_pass_report_fails_criterion(tmp_path: Path) -> None:
    _write_all(tmp_path)
    spec = next(s for s in gate.EVIDENCE_SPECS if s.gate == "windows-installer-gate")
    report = _payload(spec)
    report["signature_status"] = gate.BLOCKED
    _write(tmp_path, spec, gate.seal_evidence(report))
    result = _run(tmp_path)
    assert result["status"] == gate.FAIL
    assert any(row["cause"] == "criterion_failed:code_signing" for row in result["failures"])


def test_atomic_report_and_masterplan_reflect_real_result(tmp_path: Path) -> None:
    _write_all(tmp_path)
    masterplan = tmp_path / gate.MASTERPLAN_PATH
    masterplan.parent.mkdir(parents=True)
    masterplan.write_text(json.dumps({
        "release_readiness": {"state": "BLOCKED", "missing_gates": ["jarvis-1.0-gate"]},
        "live_gates": {"missing": ["jarvis-1.0-gate"], "certified": []},
    }), encoding="utf-8")
    report = gate.run_jarvis_1_0_gate(
        tmp_path, commit_sha=COMMIT, now=NOW,
        write_report=True, update_masterplan=True,
    )
    persisted = json.loads((tmp_path / gate.REPORT_PATH).read_text(encoding="utf-8"))
    updated = json.loads(masterplan.read_text(encoding="utf-8"))
    assert persisted["status"] == gate.PASS
    assert persisted["report_sha256"] == gate.aggregate_hash(persisted)
    assert updated["release_readiness"]["state"] == "READY"
    assert updated["jarvis_1_0_certification"]["status"] == gate.PASS
    assert not list((tmp_path / "runtime/reports").glob("*.tmp"))


def test_masterplan_never_claims_ready_for_blocked_gate(tmp_path: Path) -> None:
    masterplan = tmp_path / gate.MASTERPLAN_PATH
    masterplan.parent.mkdir(parents=True)
    masterplan.write_text(json.dumps({
        "release_readiness": {"state": "READY", "missing_gates": ["jarvis-1.0-gate"]},
        "live_gates": {
            "missing": ["jarvis-1.0-gate"],
            "certified": ["jarvis-1.0-gate"],
        },
    }), encoding="utf-8")
    report = gate.run_jarvis_1_0_gate(
        tmp_path, commit_sha=COMMIT, now=NOW,
        write_report=True, update_masterplan=True,
    )
    updated = json.loads(masterplan.read_text(encoding="utf-8"))
    assert report["status"] == gate.BLOCKED
    assert updated["release_readiness"]["state"] == "BLOCKED"
    assert "jarvis-1.0-gate" not in updated["live_gates"]["certified"]
    assert "jarvis-1.0-gate" in updated["live_gates"]["implemented_not_certified"]


def test_report_contains_no_source_payload_or_secrets(tmp_path: Path) -> None:
    _write_all(tmp_path)
    spec = gate.EVIDENCE_SPECS[0]
    source = _payload(spec)
    source["password"] = "do-not-leak"
    _write(tmp_path, spec, gate.seal_evidence(source))
    serialized = json.dumps(_run(tmp_path))
    assert "do-not-leak" not in serialized
    assert "password" not in serialized
