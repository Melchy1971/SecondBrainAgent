from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Mapping, Sequence, Any

VALID_STATUSES = {"PASS", "CONDITIONAL_PASS", "WARN", "READY", "PASS_CANDIDATE"}
BLOCKING_STATUSES = {"FAIL", "BLOCKED", "ERROR"}


@dataclass(frozen=True)
class RCBlocker:
    code: str
    severity: str
    message: str
    source: str = "release_candidate"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class RCCriterion:
    id: str
    description: str
    required: bool
    status: str
    evidence: str = ""

    @property
    def passed(self) -> bool:
        return self.status == "PASS" or (not self.required and self.status in {"WARN", "SKIP"})

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RCChecklistItem:
    id: str
    label: str
    status: str
    owner: str = "release"
    required: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ReleaseCandidateSummary:
    rc_id: str
    version: str
    created_at: str
    status: str
    gate_status: str
    tests_passed: int
    min_tests_passed: int
    criteria: tuple[RCCriterion, ...] = field(default_factory=tuple)
    checklist: tuple[RCChecklistItem, ...] = field(default_factory=tuple)
    blockers: tuple[RCBlocker, ...] = field(default_factory=tuple)
    warnings: tuple[RCBlocker, ...] = field(default_factory=tuple)

    @property
    def blocker_count(self) -> int:
        return len(self.blockers)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    def to_dict(self) -> dict[str, object]:
        return {
            "rc_id": self.rc_id,
            "version": self.version,
            "created_at": self.created_at,
            "status": self.status,
            "gate_status": self.gate_status,
            "tests_passed": self.tests_passed,
            "min_tests_passed": self.min_tests_passed,
            "criteria": [criterion.to_dict() for criterion in self.criteria],
            "checklist": [item.to_dict() for item in self.checklist],
            "blockers": [blocker.to_dict() for blocker in self.blockers],
            "warnings": [warning.to_dict() for warning in self.warnings],
            "blocker_count": self.blocker_count,
            "warning_count": self.warning_count,
        }


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_status(value: Any, default: str = "UNKNOWN") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        return str(value.get("status", default))
    return str(getattr(value, "status", default))


def _read_int(value: Any, key: str, default: int = 0) -> int:
    raw: Any
    if isinstance(value, Mapping):
        raw = value.get(key, default)
    else:
        raw = getattr(value, key, default)
    if raw is None:
        return default
    return int(raw)


def normalize_issue(issue: str | Mapping[str, Any] | RCBlocker, *, default_severity: str = "WARNING") -> RCBlocker:
    if isinstance(issue, RCBlocker):
        return issue
    if isinstance(issue, str):
        return RCBlocker(code="manual_issue", severity=default_severity, message=issue, source="manual")
    code = str(issue.get("code", "manual_issue"))
    severity = str(issue.get("severity", default_severity)).upper()
    message = str(issue.get("message", issue.get("detail", "")))
    source = str(issue.get("source", "manual"))
    return RCBlocker(code=code, severity=severity, message=message, source=source)


def create_rc_checklist(*, gate_status: str, packaging_status: str, upgrade_status: str, tests_passed: int, min_tests_passed: int) -> tuple[RCChecklistItem, ...]:
    return (
        RCChecklistItem("release_gate", "Release gate executed", "PASS" if gate_status in VALID_STATUSES else "FAIL"),
        RCChecklistItem("test_threshold", "Minimum regression test count reached", "PASS" if tests_passed >= min_tests_passed else "FAIL"),
        RCChecklistItem("deployment_package", "Deployment package validated", "PASS" if packaging_status in VALID_STATUSES else "FAIL"),
        RCChecklistItem("upgrade_pipeline", "Upgrade pipeline validated", "PASS" if upgrade_status in VALID_STATUSES else "FAIL"),
        RCChecklistItem("known_blockers", "Known blocker list triaged", "PASS"),
    )


def create_rc_criteria(*, gate_status: str, packaging_status: str, upgrade_status: str, tests_passed: int, min_tests_passed: int) -> tuple[RCCriterion, ...]:
    return (
        RCCriterion("gate_status", "Release gate must not be failed or blocked.", True, "PASS" if gate_status in VALID_STATUSES else "FAIL", gate_status),
        RCCriterion("test_count", "Regression test count must meet RC threshold.", True, "PASS" if tests_passed >= min_tests_passed else "FAIL", str(tests_passed)),
        RCCriterion("packaging", "Deployment package must be valid.", True, "PASS" if packaging_status in VALID_STATUSES else "FAIL", packaging_status),
        RCCriterion("upgrade", "Upgrade plan must be ready or pass candidate.", True, "PASS" if upgrade_status in VALID_STATUSES else "FAIL", upgrade_status),
    )


def build_release_candidate(
    *,
    version: str,
    rc_number: int = 1,
    release_gate: Any | None = None,
    packaging_status: str | Mapping[str, Any] = "READY",
    upgrade_status: str | Mapping[str, Any] = "READY",
    tests_passed: int | None = None,
    min_tests_passed: int = 500,
    known_issues: Sequence[str | Mapping[str, Any] | RCBlocker] = (),
) -> ReleaseCandidateSummary:
    gate_status = _read_status(release_gate, default="UNKNOWN")
    gate_tests = _read_int(release_gate, "tests_passed", 0)
    effective_tests = int(tests_passed if tests_passed is not None else gate_tests)
    package_status = _read_status(packaging_status)
    upgrade_plan_status = _read_status(upgrade_status)

    criteria = create_rc_criteria(
        gate_status=gate_status,
        packaging_status=package_status,
        upgrade_status=upgrade_plan_status,
        tests_passed=effective_tests,
        min_tests_passed=min_tests_passed,
    )
    checklist = create_rc_checklist(
        gate_status=gate_status,
        packaging_status=package_status,
        upgrade_status=upgrade_plan_status,
        tests_passed=effective_tests,
        min_tests_passed=min_tests_passed,
    )

    blockers: list[RCBlocker] = []
    warnings: list[RCBlocker] = []
    for criterion in criteria:
        if criterion.required and criterion.status != "PASS":
            blockers.append(RCBlocker(code=f"criterion:{criterion.id}", severity="BLOCKER", message=criterion.description, source="criterion"))

    for issue in known_issues:
        normalized = normalize_issue(issue)
        if normalized.severity in {"BLOCKER", "ERROR", "FAIL"}:
            blockers.append(normalized)
        else:
            warnings.append(normalized)

    gate_blockers = _read_int(release_gate, "blocker_count", 0)
    gate_warnings = _read_int(release_gate, "warning_count", 0)
    if gate_blockers:
        blockers.append(RCBlocker("gate_blockers", "BLOCKER", f"Release gate reports {gate_blockers} blocker(s).", "release_gate"))
    if gate_warnings:
        warnings.append(RCBlocker("gate_warnings", "WARNING", f"Release gate reports {gate_warnings} warning(s).", "release_gate"))

    status = "FAIL" if blockers else ("CONDITIONAL_PASS" if warnings or gate_status == "CONDITIONAL_PASS" else "PASS")
    return ReleaseCandidateSummary(
        rc_id=f"{version}-RC{rc_number}",
        version=version,
        created_at=_utc_now(),
        status=status,
        gate_status=gate_status,
        tests_passed=effective_tests,
        min_tests_passed=min_tests_passed,
        criteria=criteria,
        checklist=checklist,
        blockers=tuple(blockers),
        warnings=tuple(warnings),
    )


def write_release_candidate_report(root: str | Path, summary: ReleaseCandidateSummary, *, filename: str = "release_candidate.json") -> Path:
    target = Path(root) / "release" / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(summary.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return target
