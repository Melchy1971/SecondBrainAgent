from pathlib import Path

from secondbrain.desktop.documents.rc import (
    DocumentCenterRCGate,
    DocumentCenterRCReportWriter,
    GateStatus,
    default_rc1_capability_state,
    summarize_result,
)


def test_default_document_center_rc1_passes() -> None:
    result = DocumentCenterRCGate().evaluate(default_rc1_capability_state())

    assert result.status == GateStatus.PASS
    assert result.ready_count == result.total_count
    assert result.findings == []


def test_missing_required_capability_fails() -> None:
    state = default_rc1_capability_state()
    state["preview"] = {"implemented": False, "tested": False}

    result = DocumentCenterRCGate().evaluate(state)

    assert result.status == GateStatus.FAIL
    assert any(finding.code == "DOCUMENT_CENTER_CAPABILITY_MISSING" for finding in result.findings)


def test_implemented_but_untested_is_conditional_pass() -> None:
    state = default_rc1_capability_state()
    state["bulk_workflows"] = {"implemented": True, "tested": False}

    result = DocumentCenterRCGate().evaluate(state)

    assert result.status == GateStatus.CONDITIONAL_PASS
    assert any(finding.code == "DOCUMENT_CENTER_TEST_COVERAGE_MISSING" for finding in result.findings)


def test_user_safety_risk_fails_gate() -> None:
    state = default_rc1_capability_state()
    state["detail_view"] = {"implemented": True, "tested": True, "user_safe": False}

    result = DocumentCenterRCGate().evaluate(state)

    assert result.status == GateStatus.FAIL
    assert any(finding.code == "DOCUMENT_CENTER_USER_SAFETY_RISK" for finding in result.findings)


def test_report_writer_writes_json_and_markdown(tmp_path: Path) -> None:
    result = DocumentCenterRCGate().evaluate(default_rc1_capability_state())
    writer = DocumentCenterRCReportWriter(tmp_path)

    json_path = writer.write_json(result)
    markdown_path = writer.write_markdown(result)

    assert json_path.exists()
    assert markdown_path.exists()
    assert "PASS" in json_path.read_text(encoding="utf-8")
    assert "Document Center RC1 Gate" in markdown_path.read_text(encoding="utf-8")


def test_summary_counts_findings() -> None:
    result = DocumentCenterRCGate().evaluate(default_rc1_capability_state())

    summary = summarize_result(result)

    assert summary == {"status": "PASS", "ready": 8, "total": 8, "blockers": 0, "warnings": 0}
