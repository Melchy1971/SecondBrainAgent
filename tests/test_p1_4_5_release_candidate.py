import json

from secondbrain.release.release_candidate import (
    RCBlocker,
    build_release_candidate,
    create_rc_checklist,
    normalize_issue,
    write_release_candidate_report,
)


def test_release_candidate_passes_with_green_gate_and_threshold():
    rc = build_release_candidate(
        version="P1.4.5",
        release_gate={"status": "PASS", "tests_passed": 519, "blocker_count": 0, "warning_count": 0},
        packaging_status="READY",
        upgrade_status="READY",
        min_tests_passed=500,
    )

    assert rc.rc_id == "P1.4.5-RC1"
    assert rc.status == "PASS"
    assert rc.blocker_count == 0
    assert all(item.status == "PASS" for item in rc.checklist)


def test_release_candidate_blocks_when_test_threshold_is_not_met():
    rc = build_release_candidate(
        version="P1.4.5",
        release_gate={"status": "PASS", "tests_passed": 499},
        min_tests_passed=500,
    )

    assert rc.status == "FAIL"
    assert any(blocker.code == "criterion:test_count" for blocker in rc.blockers)


def test_release_candidate_blocks_failed_packaging():
    rc = build_release_candidate(
        version="P1.4.5",
        release_gate={"status": "PASS", "tests_passed": 520},
        packaging_status="FAIL",
        upgrade_status="READY",
    )

    assert rc.status == "FAIL"
    assert any(blocker.code == "criterion:packaging" for blocker in rc.blockers)


def test_release_candidate_keeps_warnings_as_conditional_pass():
    rc = build_release_candidate(
        version="P1.4.5",
        release_gate={"status": "CONDITIONAL_PASS", "tests_passed": 520, "warning_count": 1},
        known_issues=[{"code": "doc_gap", "severity": "warning", "message": "Minor documentation lag"}],
    )

    assert rc.status == "CONDITIONAL_PASS"
    assert rc.blocker_count == 0
    assert rc.warning_count == 2


def test_manual_blocker_forces_fail():
    rc = build_release_candidate(
        version="P1.4.5",
        release_gate={"status": "PASS", "tests_passed": 520},
        known_issues=[RCBlocker("security_gap", "BLOCKER", "Security acceptance missing", "manual")],
    )

    assert rc.status == "FAIL"
    assert any(blocker.code == "security_gap" for blocker in rc.blockers)


def test_normalize_issue_accepts_string_and_mapping():
    string_issue = normalize_issue("Needs review")
    mapping_issue = normalize_issue({"code": "x", "severity": "blocker", "message": "Broken", "source": "test"})

    assert string_issue.severity == "WARNING"
    assert string_issue.source == "manual"
    assert mapping_issue.code == "x"
    assert mapping_issue.severity == "BLOCKER"


def test_create_rc_checklist_marks_failed_upgrade():
    checklist = create_rc_checklist(gate_status="PASS", packaging_status="READY", upgrade_status="BLOCKED", tests_passed=520, min_tests_passed=500)

    failed = [item for item in checklist if item.status == "FAIL"]
    assert len(failed) == 1
    assert failed[0].id == "upgrade_pipeline"


def test_write_release_candidate_report(tmp_path):
    rc = build_release_candidate(version="P1.4.5", release_gate={"status": "PASS", "tests_passed": 520})

    path = write_release_candidate_report(tmp_path, rc)
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert path.name == "release_candidate.json"
    assert payload["rc_id"] == "P1.4.5-RC1"
    assert payload["status"] == "PASS"
