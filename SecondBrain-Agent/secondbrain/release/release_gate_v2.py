from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json

from .consistency_validator import ConsistencyReport, validate_release_consistency
from .manifest_generator import ReleaseManifestV2, generate_manifest, write_manifest
from .build_info import write_build_info


@dataclass(frozen=True)
class ReleaseGateV2Result:
    version: str
    status: str
    manifest_status: str
    consistency_status: str
    tests_passed: int | None
    blocker_count: int
    warning_count: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def evaluate_release_gate(root: str | Path, *, version: str, min_tests_passed: int = 500) -> ReleaseGateV2Result:
    base = Path(root)
    manifest: ReleaseManifestV2 = generate_manifest(base, version=version, status="PASS_CANDIDATE")
    consistency: ConsistencyReport = validate_release_consistency(base, expected_version=version)

    blockers = 0
    warnings = 0
    if manifest.highest_passed is None or manifest.highest_passed < min_tests_passed:
        blockers += 1
    for issue in consistency.issues:
        if issue.severity == "ERROR":
            blockers += 1
        else:
            warnings += 1

    status = "FAIL" if blockers else ("CONDITIONAL_PASS" if warnings else "PASS")
    return ReleaseGateV2Result(
        version=version,
        status=status,
        manifest_status=manifest.status,
        consistency_status=consistency.status,
        tests_passed=manifest.highest_passed,
        blocker_count=blockers,
        warning_count=warnings,
    )


def write_release_gate_outputs(root: str | Path, *, version: str, min_tests_passed: int = 500) -> Path:
    base = Path(root)
    write_build_info(base, version=version)
    write_manifest(base, version=version)
    result = evaluate_release_gate(base, version=version, min_tests_passed=min_tests_passed)
    target = base / "release" / "release_gate.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return target
