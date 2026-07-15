from __future__ import annotations

import json
from pathlib import Path

from secondbrain.release.ga_readiness import (
    BLOCKED,
    CONDITIONAL_PASS,
    GROUPS,
    PASS,
    Check,
    evaluate_ga_readiness,
    run_ga_readiness_gate,
)


def _green_checks() -> list[Check]:
    return [Check(f"{group}_ok", group, PASS, True, "validated") for group in GROUPS]


def test_pass_requires_all_critical_groups_green():
    report = evaluate_ga_readiness(_green_checks())
    assert report["overall_status"] == PASS
    assert set(report["component_status"]) == set(GROUPS)
    assert report["blockers"] == []
    assert report["release_recommendation"] == "Freigabe als stable"


def test_only_noncritical_warning_can_be_conditional_pass():
    checks = _green_checks() + [Check("ux_warning", "gui", CONDITIONAL_PASS, False, "minor spacing")]
    report = evaluate_ga_readiness(checks)
    assert report["overall_status"] == CONDITIONAL_PASS
    assert report["blockers"] == [] and report["warnings"][0]["check_id"] == "ux_warning"


def test_critical_failure_blocks_release():
    checks = _green_checks() + [Check("signed_update_rollback", "operations", BLOCKED, True, "unsigned update")]
    report = evaluate_ga_readiness(checks)
    assert report["overall_status"] == BLOCKED
    assert report["blockers"][0]["check_id"] == "signed_update_rollback"
    assert "signed_update_rollback" in report["hard_blocker_classes"]


def test_gate_writes_required_json_and_markdown_reports(tmp_path: Path):
    report = run_ga_readiness_gate(tmp_path, checks=_green_checks())
    json_path = tmp_path / "runtime/reports/ga_readiness.json"
    markdown_path = tmp_path / "docs/releases/v31_04_ga_readiness.md"
    assert json.loads(json_path.read_text(encoding="utf-8"))["overall_status"] == PASS
    assert "Overall status: **PASS**" in markdown_path.read_text(encoding="utf-8")
    required = {
        "overall_status", "component_status", "blockers", "warnings", "security_summary",
        "data_summary", "quality_summary", "performance_summary", "installer_summary",
        "recovery_summary", "open_risks", "release_recommendation",
    }
    assert required <= report.keys()


def test_launcher_exposes_single_ga_gate_and_required_existing_aliases():
    launcher = (Path(__file__).resolve().parents[1] / "launcher.py").read_text(encoding="utf-8")
    for command in ("ga-readiness-gate", "security-gate", "backup-gate", "system-rc-gate", "review-approval-release-gate", "rag-eval"):
        assert f'cmd == "{command}"' in launcher
