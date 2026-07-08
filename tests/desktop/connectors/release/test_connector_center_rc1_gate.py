from pathlib import Path

from secondbrain.desktop.connectors.release import ConnectorCenterRC1Gate, ConnectorCenterMetrics
from secondbrain.desktop.connectors.release.connector_center_checklist import ConnectorCenterChecklist


def test_connector_center_rc1_gate_passes_with_all_capabilities():
    result = ConnectorCenterRC1Gate().run(
        ConnectorCenterChecklist.REQUIRED_KEYS,
        ConnectorCenterMetrics(total_connectors=2, enabled_connectors=1, disabled_connectors=1, healthy_connectors=2),
    )
    assert result.passed is True
    assert result.status == "PASS"
    assert result.report.checklist_summary["PASS"] == len(ConnectorCenterChecklist.REQUIRED_KEYS)


def test_connector_center_rc1_gate_fails_when_required_capability_missing():
    result = ConnectorCenterRC1Gate().run(["center_service"])
    assert result.passed is False
    assert result.status == "FAIL"
    assert any(issue.code.startswith("missing_") for issue in result.issues)


def test_connector_center_rc1_gate_warns_on_failed_jobs():
    result = ConnectorCenterRC1Gate().run(
        ConnectorCenterChecklist.REQUIRED_KEYS,
        ConnectorCenterMetrics(total_connectors=1, enabled_connectors=1, healthy_connectors=1, failed_jobs=1),
    )
    assert result.status == "WARNING"
    assert any(issue.code == "failed_jobs_present" for issue in result.issues)


def test_connector_center_rc1_gate_writes_reports(tmp_path: Path):
    result = ConnectorCenterRC1Gate().run(ConnectorCenterChecklist.REQUIRED_KEYS)
    files = ConnectorCenterRC1Gate().write_reports(result, tmp_path)
    assert set(files) == {"connector_rc1_report", "connector_metrics", "connector_validation", "connector_checklist"}
    assert all(path.exists() for path in files.values())
    assert '"status": "PASS"' in files["connector_rc1_report"].read_text(encoding="utf-8")
