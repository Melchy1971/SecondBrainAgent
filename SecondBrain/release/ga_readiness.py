"""Single fail-closed GA release gate aggregating existing system gates."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
from uuid import uuid4

PASS = "PASS"
CONDITIONAL_PASS = "CONDITIONAL_PASS"
BLOCKED = "BLOCKED"
REPORT_PATH = Path("runtime/reports/ga_readiness.json")
DOC_PATH = Path("docs/releases/v31_04_ga_readiness.md")

GROUPS = ("build", "security", "data", "rag", "operations", "gui", "performance", "privacy")
HARD_BLOCKERS = {
    "security_gate", "review_approval_gate", "backup_restore", "installer_smoke",
    "signed_update_rollback", "rag_production", "postgres_pgvector", "full_test_suite",
    "privacy_governance", "data_integrity_migrations",
}


@dataclass(frozen=True)
class Check:
    check_id: str
    group: str
    status: str
    critical: bool
    summary: str
    evidence: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {"check_id": self.check_id, "group": self.group, "status": self.status,
                "critical": self.critical, "summary": self.summary, "evidence": self.evidence}


def _status(value: Any) -> str:
    raw = str(value or "").upper()
    if raw in {"PASS", "PASSED", "OK", "READY", "CURRENT", "SUCCESS"}:
        return PASS
    if raw in {"CONDITIONAL_PASS", "WARNING", "WARN", "DEGRADED"}:
        return CONDITIONAL_PASS
    return BLOCKED


def _probe(check_id: str, group: str, critical: bool, fn: Callable[[], tuple[Any, str, Any]]) -> Check:
    try:
        status, summary, evidence = fn()
        return Check(check_id, group, _status(status), critical, str(summary), evidence)
    except Exception as exc:  # noqa: BLE001 - every gate failure is controlled and fail-closed
        return Check(check_id, group, BLOCKED, critical, f"controlled_error:{type(exc).__name__}")


def _json_evidence(root: Path, relative: str) -> dict[str, Any] | None:
    path = root / relative
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def collect_existing_gates(project_root: str | Path) -> list[Check]:
    root = Path(project_root).resolve()
    checks: list[Check] = []

    from secondbrain.release.repo_doctor import run_repo_doctor
    from secondbrain.runtime_config.service import RuntimeConfig
    from secondbrain.security_gate_v3095 import run_security_gate
    from secondbrain.backup_gate_v3096 import run_backup_gate
    from secondbrain.release.rc_gate import run_rc_gate
    from secondbrain.agent.review_approval_release_gate import run_review_approval_release_gate
    from secondbrain.p1_rag_runtime import P1RagRuntime
    from secondbrain.p1_production_gate import production_gate_with_golden
    from secondbrain.p3_pgvector_foundation import pgvector_readiness

    repo = _probe("repo_doctor", "build", True, lambda: (
        PASS if (value := run_repo_doctor(root, execute_runtime_checks=True).to_dict()).get("ok") else BLOCKED,
        "existing Repo Doctor", value))
    checks.append(repo)
    checks.append(_probe("config_doctor", "operations", True, lambda: (
        PASS if (value := RuntimeConfig(root).startup_status()).get("status") != "blocked" else BLOCKED,
        "existing Config Doctor", value)))
    checks.append(_probe("security_gate", "security", True, lambda: (
        (value := run_security_gate(root))["status"], "existing Security Gate", value)))
    checks.append(_probe("review_approval_gate", "security", True, lambda: (
        (value := run_review_approval_release_gate(root))["overall_status"],
        "existing Review/Approval release gate", value)))
    checks.append(_probe("backup_restore", "data", True, lambda: (
        (value := run_backup_gate(root))["status"], "existing Backup/Restore gate", value)))
    checks.append(_probe("system_rc_gate", "operations", True, lambda: (
        (value := run_rc_gate(root))["verdict"], "existing system RC gate", value)))

    rag_runtime = P1RagRuntime(root)
    checks.append(_probe("rag_production", "rag", True, lambda: (
        PASS if (value := production_gate_with_golden(rag_runtime, root, write_report=True)).get("ok") else BLOCKED,
        "provider, golden dataset, MRR, nDCG, citations and index", value)))
    checks.append(_probe("postgres_pgvector", "data", True, lambda: (
        PASS if (
            (value := pgvector_readiness(root, write_report=True, live=True)).get("ok")
            and value.get("config", {}).get("enabled")
            and value.get("config", {}).get("dsn")
            and value.get("live", {}).get("status") == "pass"
        ) else BLOCKED,
        "PostgreSQL/pgvector production readiness", value)))

    release_dir = root / "dist" / "release"
    artifact_names = {path.name for path in release_dir.glob("*")} if release_dir.is_dir() else set()
    required_fragments = ("portable-win64.zip", "Setup-", ".msi", "SHA256SUMS.txt", "sbom.cdx.json", "release-manifest.json")
    missing = [fragment for fragment in required_fragments if not any(fragment in name for name in artifact_names)]
    checks.append(Check("packaging", "build", BLOCKED if missing else PASS, True,
                        "Windows packaging artifacts", {"missing": missing, "artifacts": sorted(artifact_names)}))

    installer = _json_evidence(root, "runtime/reports/installer_smoke.json")
    checks.append(Check("installer_smoke", "build", _status(installer and installer.get("status")), True,
                        "fresh install, first start, repair, uninstall and portable", installer))
    update = _json_evidence(root, "runtime/reports/update_smoke.json")
    checks.append(Check("signed_update_rollback", "operations", _status(update and update.get("status")), True,
                        "signed update and rollback smoke", update))
    performance = _json_evidence(root, "runtime/reports/load_small.json")
    checks.append(Check("performance_small", "performance", _status(performance and performance.get("status")), True,
                        "small load, regression, deadlock, OOM and GUI freeze", performance))
    full_tests = _json_evidence(root, "runtime/reports/full_pytest.json")
    checks.append(Check("full_test_suite", "operations", _status(full_tests and full_tests.get("status")), True,
                        "complete pytest suite evidence", full_tests))

    # Existing certification reports are the source of truth for GUI/privacy/operations.
    evidence_map = {
        "gui_centers": ("gui", "runtime/reports/gui_smoke.json", True),
        "privacy_governance": ("privacy", "runtime/reports/privacy_gate.json", True),
        "operations_recovery": ("operations", "runtime/reports/operations_smoke.json", True),
        "data_integrity_migrations": ("data", "runtime/reports/data_integrity.json", True),
    }
    for check_id, (group, path, critical) in evidence_map.items():
        evidence = _json_evidence(root, path)
        checks.append(Check(check_id, group, _status(evidence and evidence.get("status")), critical,
                            f"existing evidence: {path}", evidence))
    return checks


def evaluate_ga_readiness(checks: list[Check]) -> dict[str, Any]:
    components: dict[str, str] = {}
    for group in GROUPS:
        rows = [check for check in checks if check.group == group]
        components[group] = (BLOCKED if any(row.status == BLOCKED and row.critical for row in rows)
                             else CONDITIONAL_PASS if any(row.status != PASS for row in rows) else PASS)
    blockers = [check.to_dict() for check in checks if check.status == BLOCKED and check.critical]
    warnings = [check.to_dict() for check in checks if check.status != PASS and not (check.status == BLOCKED and check.critical)]
    hard_ids = sorted({check["check_id"] for check in blockers} & HARD_BLOCKERS)
    overall = BLOCKED if blockers else (CONDITIONAL_PASS if warnings else PASS)
    by_group = {group: [check.to_dict() for check in checks if check.group == group] for group in GROUPS}
    return {
        "schema": "secondbrain.ga_readiness.v31_04",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "overall_status": overall,
        "component_status": components,
        "blockers": blockers,
        "warnings": warnings,
        "security_summary": by_group["security"],
        "data_summary": by_group["data"],
        "quality_summary": by_group["rag"] + by_group["gui"] + [c.to_dict() for c in checks if c.check_id == "full_test_suite"],
        "performance_summary": by_group["performance"],
        "installer_summary": [c.to_dict() for c in checks if c.check_id in {"packaging", "installer_smoke"}],
        "recovery_summary": [c.to_dict() for c in checks if "recovery" in c.check_id or "rollback" in c.check_id or c.check_id == "backup_restore"],
        "open_risks": sorted({c["check_id"] for c in blockers + warnings}),
        "hard_blocker_classes": hard_ids,
        "release_recommendation": ("Freigabe als stable" if overall == PASS else
                                   "Freigabe nur nach Bewertung nichtkritischer Warnungen" if overall == CONDITIONAL_PASS else
                                   "Keine GA-Freigabe; kritische Evidenz fehlt oder ist rot"),
        "checks": [check.to_dict() for check in checks],
    }


def _markdown(report: Mapping[str, Any]) -> str:
    lines = ["# Jarvis v31.04 GA Readiness", "", f"Overall status: **{report['overall_status']}**", "",
             "## Components", "", "| Component | Status |", "|---|---|"]
    lines.extend(f"| {name} | {status} |" for name, status in report["component_status"].items())
    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- `{row['check_id']}`: {row['summary']}" for row in report["blockers"])
    if not report["blockers"]:
        lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- `{row['check_id']}`: {row['summary']}" for row in report["warnings"])
    if not report["warnings"]:
        lines.append("- None")
    lines.extend(["", "## Release recommendation", "", str(report["release_recommendation"]), ""])
    return "\n".join(lines)


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def run_ga_readiness_gate(project_root: str | Path = ".", *, checks: list[Check] | None = None,
                          write_reports: bool = True) -> dict[str, Any]:
    root = Path(project_root).resolve()
    report = evaluate_ga_readiness(checks if checks is not None else collect_existing_gates(root))
    if write_reports:
        _atomic_write(root / REPORT_PATH, json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
        _atomic_write(root / DOC_PATH, _markdown(report))
    return report


__all__ = ["BLOCKED", "CONDITIONAL_PASS", "PASS", "Check", "evaluate_ga_readiness", "run_ga_readiness_gate"]
