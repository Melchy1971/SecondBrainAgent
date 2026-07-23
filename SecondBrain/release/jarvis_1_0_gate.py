"""Strict Jarvis 1.0 evidence aggregator.

This gate never executes or simulates a subordinate gate. It only validates
already persisted, commit-bound and integrity-protected reports.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
from uuid import uuid4

PASS, BLOCKED, FAIL, SKIPPED, CONDITIONAL_PASS = (
    "PASS", "BLOCKED", "FAIL", "SKIPPED", "CONDITIONAL_PASS",
)
SCHEMA = "secondbrain.jarvis_1_0_gate.v1"
REPORT_PATH = Path("runtime/reports/jarvis_1_0_gate.json")
MASTERPLAN_PATH = Path("docs/09_MASTERPLAN_STATUS.json")


@dataclass(frozen=True)
class EvidenceSpec:
    gate: str
    path: str
    schema: str
    environment: str
    criteria: tuple[str, ...]
    required_phases: tuple[str, ...] = ()


EVIDENCE_SPECS = (
    EvidenceSpec(
        "postgres-live-gate", "runtime/reports/postgres_live_gate.json",
        "secondbrain.postgres_live_gate.v1", "production",
        ("postgresql_tls_verify_full", "postgres_live_gate", "repository_contracts",
         "workspace_isolation"),
        ("preflight", "isolated_schema", "repository_contracts", "workspace_isolation",
         "concurrency", "vector_search_recall", "report"),
    ),
    EvidenceSpec(
        "review-approval-postgresql", "runtime/reports/approval_postgres_live_gate.json",
        "secondbrain.approval_postgres_live_gate.v1", "production",
        ("review_approval_postgresql",),
    ),
    EvidenceSpec(
        "provider-live-gate", "runtime/reports/provider_live_gate.json",
        "secondbrain.provider_live_gate.v1", "production", ("provider_live_gate",),
    ),
    EvidenceSpec(
        "connector-e2e-gate", "runtime/reports/connector_e2e_gate.json",
        "secondbrain.connector_e2e_gate.v1", "production",
        ("release_connectors_e2e",),
    ),
    EvidenceSpec(
        "runtime-architecture-gate", "runtime/reports/runtime_architecture_gate.json",
        "secondbrain.runtime_architecture_gate.v1", "production",
        ("canonical_job_runtime", "no_jsonl_production_fallback",
         "no_parallel_production_subsystems"),
    ),
    EvidenceSpec(
        "native-voice-app-gate", "runtime/reports/native_voice_app_gate.json",
        "secondbrain.native_voice_app_gate.v31_79", "production",
        ("desktop_gate", "voice_gate"),
    ),
    EvidenceSpec(
        "disaster-recovery-gate", "runtime/reports/disaster_recovery_gate.json",
        "secondbrain.disaster_recovery_gate.v1", "production",
        ("disaster_recovery",),
        ("snapshot_before_restore", "full_backup", "backup_checksum_valid",
         "full_restore_matches_backup", "rollback_restores_prior_state",
         "pg_restore_into_empty_database"),
    ),
    EvidenceSpec(
        "os-keyring-gate", "runtime/reports/os_keyring_gate.json",
        "secondbrain.os_keyring_gate.v1", "production", ("os_keyring",),
    ),
    EvidenceSpec(
        "windows-installer-gate", "runtime/reports/windows_installer_gate.json",
        "secondbrain.windows-installer-gate.v1", "clean-windows",
        ("windows_installer_gate", "code_signing"),
        ("preflight", "clean_build", "artifact_inventory", "hash_generation",
         "signature_verification", "silent_install", "desktop_shortcut",
         "application_start", "health_check", "upgrade", "rollback", "uninstall",
         "residue_check", "report"),
    ),
    EvidenceSpec(
        "full-test-suite", "runtime/reports/full_pytest.json",
        "secondbrain.full_pytest.v1", "ci", ("full_test_suite",),
    ),
    EvidenceSpec(
        "version-sync-gate", "runtime/reports/version_sync.json",
        "secondbrain.version_sync.v1", "ci", ("masterplan_package_version_sync",),
    ),
    EvidenceSpec(
        "ci-commit-gate", "runtime/reports/ci_current_commit.json",
        "secondbrain.ci_current_commit.v1", "ci", ("current_commit_ci_verified",),
    ),
)


def canonical_hash(report: Mapping[str, Any]) -> str:
    payload = {key: value for key, value in report.items() if key != "evidence_sha256"}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def seal_evidence(report: Mapping[str, Any]) -> dict[str, Any]:
    """Helper for report producers and hermetic tests."""
    sealed = dict(report)
    sealed["evidence_sha256"] = canonical_hash(sealed)
    return sealed


def aggregate_hash(report: Mapping[str, Any]) -> str:
    payload = {key: value for key, value in report.items() if key != "report_sha256"}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _parse_time(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except (TypeError, ValueError):
        return None


def _git_commit(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True,
        capture_output=True, text=True,
    )
    return result.stdout.strip()


def _status(report: Mapping[str, Any]) -> str:
    return str(report.get("status", report.get("overall_status", ""))).upper()


def _criterion_passes(name: str, report: Mapping[str, Any]) -> bool:
    if name == "postgresql_tls_verify_full":
        tls = report.get("tls", {})
        return (
            isinstance(tls, Mapping)
            and tls.get("active") is True
            and tls.get("sslmode") == "verify-full"
            and tls.get("hostname_verified") is True
        )
    if name in {"repository_contracts", "workspace_isolation"}:
        facts = report.get("facts", {})
        value = facts.get(name) if isinstance(facts, Mapping) else None
        return (
            value is True
            or isinstance(value, Mapping) and value.get("status") == PASS
        )
    if name == "release_connectors_e2e":
        required = set(report.get("release_scope_connectors", []))
        rows = {
            str(row.get("name")): str(row.get("status", "")).upper()
            for row in report.get("connectors", []) if isinstance(row, Mapping)
        }
        return bool(required) and all(rows.get(connector) == PASS for connector in required)
    if name in {
        "canonical_job_runtime", "no_jsonl_production_fallback",
        "no_parallel_production_subsystems",
    }:
        assertions = report.get("assertions", {})
        return isinstance(assertions, Mapping) and assertions.get(name) is True
    if name in {"desktop_gate", "voice_gate"}:
        components = report.get("components", {})
        component = "desktop" if name == "desktop_gate" else "voice"
        return isinstance(components, Mapping) and components.get(component) == PASS
    if name == "os_keyring":
        return (
            report.get("backend") == "os_keyring"
            and report.get("secure_backend") is True
        )
    if name == "code_signing":
        return report.get("signature_status") == PASS
    if name == "full_test_suite":
        return (
            report.get("complete") is True
            and int(report.get("failed", -1)) == 0
            and int(report.get("errors", -1)) == 0
        )
    if name == "masterplan_package_version_sync":
        return (
            report.get("synchronized") is True
            and report.get("masterplan_version") == report.get("package_version")
        )
    if name == "current_commit_ci_verified":
        return report.get("conclusion") == "success"
    return _status(report) == PASS


def _reported_phases(report: Mapping[str, Any]) -> set[str]:
    phases: set[str] = set()
    scope = report.get("scope", {})
    if isinstance(scope, Mapping):
        phases.update(str(name) for name in scope.get("implemented_phases", []))
    for key in ("phases", "checks"):
        rows = report.get(key, [])
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, Mapping) or not row.get("name"):
                continue
            passed = row.get("status") == PASS or row.get("ok") is True
            if passed:
                phases.add(str(row["name"]))
    return phases


def _problem(gate: str, cause: str, required: str) -> dict[str, str]:
    return {"gate": gate, "cause": cause, "required_evidence": required}


def _validate_evidence(
    root: Path,
    spec: EvidenceSpec,
    *,
    commit_sha: str,
    now: datetime,
    max_age: timedelta,
) -> tuple[dict[str, Any], list[dict[str, str]], list[dict[str, str]]]:
    relative = Path(spec.path)
    target = root / relative
    matrix = {
        "gate": spec.gate, "report": relative.as_posix(), "schema": spec.schema,
        "criteria": list(spec.criteria), "status": BLOCKED,
    }
    blockers: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    required = f"{spec.schema} PASS for commit {commit_sha[:12]}"
    if not target.is_file():
        blockers.append(_problem(spec.gate, "missing_report", required))
        return matrix, blockers, failures
    try:
        report = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        blockers.append(_problem(spec.gate, "unreadable_report", required))
        return matrix, blockers, failures
    if not isinstance(report, dict):
        blockers.append(_problem(spec.gate, "invalid_report_shape", required))
        return matrix, blockers, failures

    envelope_checks = (
        ("schema_mismatch", report.get("schema") == spec.schema),
        ("commit_mismatch", report.get("commit_sha") == commit_sha),
        ("environment_mismatch", report.get("environment") == spec.environment),
        ("integrity_hash_mismatch",
         isinstance(report.get("evidence_sha256"), str)
         and report.get("evidence_sha256") == canonical_hash(report)),
    )
    for cause, valid in envelope_checks:
        if not valid:
            blockers.append(_problem(spec.gate, cause, required))

    generated = _parse_time(report.get("generated_at"))
    expires = _parse_time(report.get("expires_at"))
    if generated is None:
        blockers.append(_problem(spec.gate, "invalid_generated_at", required))
    elif generated > now + timedelta(minutes=5):
        blockers.append(_problem(spec.gate, "future_report", required))
    elif now - generated > max_age:
        blockers.append(_problem(spec.gate, "stale_report", required))
    if expires is None:
        blockers.append(_problem(spec.gate, "missing_or_invalid_expiry", required))
    elif expires <= now:
        blockers.append(_problem(spec.gate, "expired_report", required))

    source_status = _status(report)
    if source_status == BLOCKED:
        blockers.append(_problem(spec.gate, "source_gate_blocked", required))
    elif source_status == FAIL:
        failures.append(_problem(spec.gate, "source_gate_failed", required))
    elif source_status in {SKIPPED, CONDITIONAL_PASS}:
        failures.append(_problem(spec.gate, f"mandatory_status_{source_status.lower()}", required))
    elif source_status != PASS:
        blockers.append(_problem(spec.gate, "unknown_source_status", required))

    if not blockers:
        missing_phases = sorted(set(spec.required_phases) - _reported_phases(report))
        if missing_phases:
            failures.append(_problem(
                spec.gate, "required_phases_missing:" + ",".join(missing_phases), required
            ))
        for criterion in spec.criteria:
            if not _criterion_passes(criterion, report):
                failures.append(_problem(spec.gate, f"criterion_failed:{criterion}", required))

    matrix["source_status"] = source_status or "UNKNOWN"
    matrix["status"] = BLOCKED if blockers else FAIL if failures else PASS
    return matrix, blockers, failures


def _atomic_json(
    path: Path, payload: Mapping[str, Any], *, sort_keys: bool = True
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, indent=2, ensure_ascii=False, sort_keys=sort_keys)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _sync_masterplan(root: Path, report: Mapping[str, Any]) -> None:
    path = root / MASTERPLAN_PATH
    if not path.is_file():
        return
    masterplan = json.loads(path.read_text(encoding="utf-8"))
    masterplan["jarvis_1_0_certification"] = {
        "status": report["status"],
        "report": REPORT_PATH.as_posix(),
        "commit_sha": report["commit_sha"],
        "evaluated_at": report["generated_at"],
    }
    readiness = masterplan.setdefault("release_readiness", {})
    readiness["state"] = "READY" if report["status"] == PASS else "BLOCKED"
    readiness["jarvis_1_0_gate"] = report["status"]
    missing = readiness.setdefault("missing_gates", [])
    readiness["missing_gates"] = [name for name in missing if name != "jarvis-1.0-gate"]
    live = masterplan.setdefault("live_gates", {})
    live_missing = live.setdefault("missing", [])
    live["missing"] = [name for name in live_missing if name != "jarvis-1.0-gate"]
    bucket = "certified" if report["status"] == PASS else "implemented_not_certified"
    opposite = "implemented_not_certified" if bucket == "certified" else "certified"
    live[opposite] = [
        name for name in live.setdefault(opposite, []) if name != "jarvis-1.0-gate"
    ]
    entries = live.setdefault(bucket, [])
    if "jarvis-1.0-gate" not in entries:
        entries.append("jarvis-1.0-gate")
    _atomic_json(path, masterplan, sort_keys=False)


def run_jarvis_1_0_gate(
    project_root: str | Path = ".",
    *,
    commit_sha: str | None = None,
    now: datetime | None = None,
    max_age_hours: int = 24,
    write_report: bool = True,
    update_masterplan: bool = True,
    specs: tuple[EvidenceSpec, ...] = EVIDENCE_SPECS,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    current_commit = commit_sha or _git_commit(root)
    evaluated_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    matrix: list[dict[str, Any]] = []
    blockers: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    for spec in specs:
        row, row_blockers, row_failures = _validate_evidence(
            root, spec, commit_sha=current_commit, now=evaluated_at,
            max_age=timedelta(hours=max_age_hours),
        )
        matrix.append(row)
        blockers.extend(row_blockers)
        failures.extend(row_failures)
    status = BLOCKED if blockers else FAIL if failures else PASS
    report: dict[str, Any] = {
        "schema": SCHEMA,
        "generated_at": evaluated_at.isoformat(),
        "commit_sha": current_commit,
        "status": status,
        "ok": status == PASS,
        "mandatory_criteria": sum((list(spec.criteria) for spec in specs), []),
        "gate_matrix": matrix,
        "blockers": blockers,
        "failures": failures,
        "source_schemas": {spec.gate: spec.schema for spec in specs},
    }
    report["report_sha256"] = aggregate_hash(report)
    if write_report:
        _atomic_json(root / REPORT_PATH, report)
        report["report"] = REPORT_PATH.as_posix()
    if update_masterplan:
        _sync_masterplan(root, report)
    return report


__all__ = [
    "BLOCKED", "CONDITIONAL_PASS", "EVIDENCE_SPECS", "EvidenceSpec", "FAIL",
    "PASS", "REPORT_PATH", "SCHEMA", "SKIPPED", "canonical_hash",
    "aggregate_hash", "run_jarvis_1_0_gate", "seal_evidence",
]
